"""Database-only email/password authentication (no .env credential bypass)."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Optional
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from .config import _PROJECT_ROOT, get_settings
from .local_auth import issue_session_tokens, login_user_payload
from .logging import get_logger
from .models import User, generate_uuid, pk_str
from .passwords import hash_password, verify_password
from .personal_workspace import ensure_personal_workspace
from .roles import PLATFORM_ROLE_SUPER_ADMIN, coerce_membership_role, normalize_membership_role
from .user_preferences import normalize_preferences

logger = get_logger('local_user_auth')

PLATFORM_ADMIN_PREF = 'platform_super_admin'


def owner_account_file_path():
    return _PROJECT_ROOT / '.tenderiq' / 'owner-account.txt'


def write_owner_account_file(
    *,
    email: str,
    password: Optional[str] = None,
    password_customized: bool = False,
) -> None:
    """Human-readable system owner credentials (gitignored under .tenderiq/)."""
    path = owner_account_file_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    if password_customized:
        body = f"""TenderIQ — System owner account

Email: {email}
Password: (you changed it in Settings — use your new password)

Sign in: http://localhost:3000/sign-in
Change password: Dashboard → Settings → Profile
"""
    else:
        body = f"""TenderIQ — System owner account (default)

Email: {email}
Password: {password}

Sign in: http://localhost:3000/sign-in
Change password: Dashboard → Settings → Profile (recommended after first login)
"""
    path.write_text(body.strip() + '\n', encoding='utf-8')


def _owner_defaults() -> tuple[str, str, str, str, str, str]:
    s = get_settings()
    owner_email = (s.SYSTEM_OWNER_EMAIL or 'admin@tendoriq.com').strip().lower()
    owner_pass = (s.SYSTEM_OWNER_DEFAULT_PASSWORD or 'Owner@ChangeMe123').strip()
    owner_name = (s.SYSTEM_OWNER_NAME or 'System Owner').strip()
    demo_email = (s.DEMO_USER_EMAIL or 'demo@tendoriq.com').strip().lower()
    demo_pass = (s.DEMO_USER_DEFAULT_PASSWORD or 'Demo@ChangeMe123').strip()
    demo_name = (s.DEMO_USER_NAME or 'Demo User').strip()
    return owner_email, owner_pass, owner_name, demo_email, demo_pass, demo_name


def _user_prefs(user: User) -> dict[str, Any]:
    return normalize_preferences(user.preferences)


def _password_hash(user: User) -> Optional[str]:
    raw = _user_prefs(user).get('password_hash')
    return raw if isinstance(raw, str) and raw.strip() else None


def _is_platform_admin(user: User) -> bool:
    return bool(_user_prefs(user).get(PLATFORM_ADMIN_PREF))


def _set_user_prefs(user: User, prefs: dict[str, Any]) -> None:
    user.preferences = normalize_preferences(prefs)


async def _resolve_tenant_session(
    db: AsyncSession,
    user: User,
) -> tuple[str, str]:
    from .account_bootstrap import resolve_db_user_session

    session = await resolve_db_user_session(db, user.email)
    if session:
        return session[2], session[3]

    return await ensure_personal_workspace(
        db,
        str(user.id),
        email=user.email,
        display_name=user.name,
    )


def _login_bundle(
    *,
    user_id: str,
    email: str,
    name: Optional[str],
    role: str,
    membership_role: Optional[str],
    tenant_id: Optional[str],
    is_super_admin: bool,
) -> tuple[dict, dict[str, Any]]:
    tokens = issue_session_tokens(
        user_id=user_id,
        email=email,
        role=role,
        tenant_id=tenant_id,
        membership_role=membership_role,
    )
    user_payload = login_user_payload(
        user_id=user_id,
        email=email,
        name=name,
        role=role,
        membership_role=membership_role,
        tenant_id=tenant_id,
        is_super_admin=is_super_admin,
    )
    return user_payload, tokens


async def authenticate_email_password(
    db: AsyncSession,
    email: str,
    password: str,
) -> Optional[tuple[dict, dict[str, Any]]]:
    """Validate credentials against users.password_hash in DB. Returns (user, tokens) or None."""
    normalized = email.strip().lower()
    if not normalized or not password:
        return None

    user = (
        await db.execute(select(User).where(User.email == normalized))
    ).scalar_one_or_none()
    if not user:
        return None

    stored = _password_hash(user)
    if not stored or not verify_password(password, stored):
        return None

    user.last_login_at = datetime.now(timezone.utc)
    await db.flush()

    if _is_platform_admin(user):
        return _login_bundle(
            user_id=str(user.id),
            email=user.email,
            name=user.name,
            role=PLATFORM_ROLE_SUPER_ADMIN,
            membership_role=None,
            tenant_id=None,
            is_super_admin=True,
        )

    tenant_id, membership_role = await _resolve_tenant_session(db, user)
    role = normalize_membership_role(membership_role) or 'member'
    return _login_bundle(
        user_id=str(user.id),
        email=user.email,
        name=user.name,
        role=role,
        membership_role=membership_role,
        tenant_id=tenant_id,
        is_super_admin=False,
    )


async def register_email_password(
    db: AsyncSession,
    *,
    email: str,
    password: str,
    name: Optional[str] = None,
    membership_role: str = 'owner',
    as_platform_admin: bool = False,
) -> tuple[dict, dict[str, Any]]:
    normalized = email.strip().lower()
    if not normalized or len(password) < 8:
        raise ValueError('Email and password (min 8 characters) are required')

    existing = (
        await db.execute(select(User).where(User.email == normalized))
    ).scalar_one_or_none()
    if existing:
        raise ValueError('An account with this email already exists')

    prefs: dict[str, Any] = {'password_hash': hash_password(password)}
    if as_platform_admin:
        prefs[PLATFORM_ADMIN_PREF] = True

    user = User(
        id=generate_uuid(),
        email=normalized,
        name=(name or normalized.split('@')[0]).strip() or 'User',
        role=coerce_membership_role(membership_role, default='member'),
        email_verified=True,
        preferences=prefs,
    )
    db.add(user)
    await db.flush()

    if as_platform_admin:
        await db.commit()
        return _login_bundle(
            user_id=str(user.id),
            email=user.email,
            name=user.name,
            role=PLATFORM_ROLE_SUPER_ADMIN,
            membership_role=None,
            tenant_id=None,
            is_super_admin=True,
        )

    tenant_id, mem_role = await ensure_personal_workspace(
        db,
        str(user.id),
        email=user.email,
        display_name=user.name,
    )
    await db.commit()
    role = normalize_membership_role(mem_role) or 'owner'
    return _login_bundle(
        user_id=str(user.id),
        email=user.email,
        name=user.name,
        role=role,
        membership_role=mem_role,
        tenant_id=tenant_id,
        is_super_admin=False,
    )


async def change_user_password(
    db: AsyncSession,
    *,
    user_id: str,
    current_password: str,
    new_password: str,
) -> None:
    if len(new_password) < 8:
        raise ValueError('New password must be at least 8 characters')

    user = await db.get(User, pk_str(user_id))
    if not user:
        raise ValueError('User not found')

    stored = _password_hash(user)
    if not stored or not verify_password(current_password, stored):
        raise ValueError('Current password is incorrect')

    prefs = _user_prefs(user)
    prefs['password_hash'] = hash_password(new_password)
    _set_user_prefs(user, prefs)
    await db.commit()

    if _is_platform_admin(user):
        write_owner_account_file(email=user.email, password_customized=True)


async def count_password_users(db: AsyncSession) -> int:
    """Users that can sign in with email/password."""
    result = await db.execute(select(func.count()).select_from(User))
    total = result.scalar() or 0
    if total == 0:
        return 0
    users = (await db.execute(select(User))).scalars().all()
    return sum(1 for u in users if _password_hash(u))


async def repair_users_missing_password_hashes(db: AsyncSession) -> bool:
    """Assign default DB passwords to users that have no password_hash yet."""
    import json

    owner_email, owner_pass, owner_name, demo_email, demo_pass, demo_name = _owner_defaults()
    targets = {
        owner_email: {
            'platform_super_admin': True,
            'name': owner_name,
            'password': owner_pass,
        },
        demo_email: {
            'platform_super_admin': False,
            'name': demo_name,
            'password': demo_pass,
        },
    }
    creds: list[dict[str, str]] = []
    changed = False

    for email, meta in targets.items():
        user = (
            await db.execute(select(User).where(User.email == email))
        ).scalar_one_or_none()
        if not user or _password_hash(user):
            continue
        password = meta['password']
        prefs = _user_prefs(user)
        prefs['password_hash'] = hash_password(password)
        if meta['platform_super_admin']:
            prefs[PLATFORM_ADMIN_PREF] = True
        _set_user_prefs(user, prefs)
        user.email_verified = True
        if not user.name:
            user.name = meta['name']
        changed = True
        creds.append(
            {
                'email': email,
                'password': password,
                'role': 'platform_admin' if meta['platform_super_admin'] else 'tenant_admin',
            }
        )
        if not meta['platform_super_admin']:
            await _resolve_tenant_session(db, user)
        if meta['platform_super_admin']:
            write_owner_account_file(email=email, password=password)

    if not changed:
        return False

    await db.commit()
    cred_path = _PROJECT_ROOT / '.tenderiq' / 'bootstrap-credentials.json'
    cred_path.parent.mkdir(parents=True, exist_ok=True)
    cred_path.write_text(
        json.dumps(
            {
                'note': 'Passwords assigned to existing accounts (no .env login).',
                'accounts': creds,
            },
            indent=2,
        ),
        encoding='utf-8',
    )
    logger.info('Repaired password hashes; see %s', cred_path)
    return True


async def _write_bootstrap_credentials(creds: list[dict[str, str]], *, note: str) -> None:
    import json

    cred_path = _PROJECT_ROOT / '.tenderiq' / 'bootstrap-credentials.json'
    cred_path.parent.mkdir(parents=True, exist_ok=True)
    cred_path.write_text(
        json.dumps({'note': note, 'accounts': creds}, indent=2),
        encoding='utf-8',
    )


async def _ensure_user_with_password(
    db: AsyncSession,
    *,
    email: str,
    password: str,
    name: str,
    platform_admin: bool,
    membership_role: str = 'owner',
) -> tuple[bool, dict[str, str]]:
    """Create user if missing. Returns (created, cred entry)."""
    user = (
        await db.execute(select(User).where(User.email == email))
    ).scalar_one_or_none()
    role_label = 'platform_admin' if platform_admin else 'tenant_admin'
    cred = {'email': email, 'password': password, 'role': role_label}

    if user:
        stored = _password_hash(user)
        if stored:
            if verify_password(password, stored):
                return False, cred
            # Dev recovery: re-sync seed accounts to .env defaults when hash drifted
            if not get_settings().is_development:
                return False, cred
            owner_email, owner_pass, _, demo_email, demo_pass, _ = _owner_defaults()
            if email not in (owner_email, demo_email) or password not in (owner_pass, demo_pass):
                return False, cred
            prefs = _user_prefs(user)
            prefs['password_hash'] = hash_password(password)
            if platform_admin:
                prefs[PLATFORM_ADMIN_PREF] = True
            _set_user_prefs(user, prefs)
            if platform_admin:
                write_owner_account_file(email=email, password=password)
            return True, cred
        prefs = _user_prefs(user)
        prefs['password_hash'] = hash_password(password)
        if platform_admin:
            prefs[PLATFORM_ADMIN_PREF] = True
        _set_user_prefs(user, prefs)
        user.email_verified = True
        if not user.name:
            user.name = name
        if platform_admin:
            write_owner_account_file(email=email, password=password)
        else:
            await _resolve_tenant_session(db, user)
        return True, cred

    prefs: dict[str, Any] = {'password_hash': hash_password(password)}
    if platform_admin:
        prefs[PLATFORM_ADMIN_PREF] = True

    user = User(
        id=generate_uuid(),
        email=email,
        name=name,
        role='admin',
        email_verified=True,
        preferences=prefs,
    )
    db.add(user)
    await db.flush()

    if platform_admin:
        write_owner_account_file(email=email, password=password)
    else:
        await _resolve_tenant_session(db, user)

    return True, cred


async def ensure_dev_accounts(db: AsyncSession) -> bool:
    """Ensure system owner + demo exist and have login passwords (idempotent)."""
    from sqlalchemy import select as sa_select

    from .config import settings
    from .models import Membership, Tenant

    owner_email, owner_pass, owner_name, demo_email, demo_pass, demo_name = _owner_defaults()
    changed = False
    creds: list[dict[str, str]] = []

    created, cred = await _ensure_user_with_password(
        db,
        email=owner_email,
        password=owner_pass,
        name=owner_name,
        platform_admin=True,
    )
    if created:
        changed = True
    creds.append(cred)

    slug = (settings.DEMO_TENANT_SLUG or 'demo').strip().lower()
    tenant = (
        await db.execute(sa_select(Tenant).where(Tenant.slug == slug))
    ).scalar_one_or_none()
    if not tenant:
        tenant = Tenant(
            id=generate_uuid(),
            name=settings.DEMO_TENANT_NAME or 'Demo Organization',
            slug=slug,
            plan='professional',
            subscription_status='active',
            status='active',
        )
        db.add(tenant)
        await db.flush()
        changed = True

    demo_user = (
        await db.execute(select(User).where(User.email == demo_email))
    ).scalar_one_or_none()
    if demo_user:
        created_demo, cred_demo = await _ensure_user_with_password(
            db,
            email=demo_email,
            password=demo_pass,
            name=demo_name,
            platform_admin=False,
        )
        if created_demo:
            changed = True
        creds.append(cred_demo)
        mem = (
            await db.execute(
                select(Membership).where(
                    Membership.user_id == demo_user.id,
                    Membership.tenant_id == tenant.id,
                )
            )
        ).scalar_one_or_none()
        if not mem:
            db.add(
                Membership(
                    user_id=demo_user.id,
                    tenant_id=tenant.id,
                    role='admin',
                    status='active',
                )
            )
            changed = True
    else:
        created_demo, cred_demo = await _ensure_user_with_password(
            db,
            email=demo_email,
            password=demo_pass,
            name=demo_name,
            platform_admin=False,
        )
        if created_demo:
            changed = True
        creds.append(cred_demo)
        demo_user = (
            await db.execute(select(User).where(User.email == demo_email))
        ).scalar_one_or_none()
        if demo_user:
            db.add(
                Membership(
                    user_id=demo_user.id,
                    tenant_id=tenant.id,
                    role='admin',
                    status='active',
                )
            )
            changed = True

    if await repair_users_missing_password_hashes(db):
        changed = True

    if changed:
        await db.commit()
        await _write_bootstrap_credentials(
            creds,
            note='Dev accounts. System owner: .tenderiq/owner-account.txt',
        )
        logger.info('Dev accounts ensured; owner login: %s', owner_account_file_path())
    return changed


async def seed_initial_accounts_if_empty(db: AsyncSession) -> bool:
    """Create system owner + demo test user when no password users exist."""
    import json

    from sqlalchemy import select as sa_select

    from .config import settings
    from .models import Membership, Tenant

    if await count_password_users(db) == 0:
        pass
    else:
        return await ensure_dev_accounts(db)

    owner_email, owner_pass, owner_name, demo_email, demo_pass, demo_name = _owner_defaults()

    admin_prefs = {
        'password_hash': hash_password(owner_pass),
        PLATFORM_ADMIN_PREF: True,
    }
    admin = User(
        id=generate_uuid(),
        email=owner_email,
        name=owner_name,
        role='admin',
        email_verified=True,
        preferences=admin_prefs,
    )
    db.add(admin)

    slug = (settings.DEMO_TENANT_SLUG or 'demo').strip().lower()
    tenant = (
        await db.execute(sa_select(Tenant).where(Tenant.slug == slug))
    ).scalar_one_or_none()
    if not tenant:
        tenant = Tenant(
            id=generate_uuid(),
            name=settings.DEMO_TENANT_NAME or 'Demo Organization',
            slug=slug,
            plan='professional',
            status='active',
        )
        db.add(tenant)
        await db.flush()

    demo = User(
        id=generate_uuid(),
        email=demo_email,
        name=demo_name,
        role='admin',
        email_verified=True,
        preferences={'password_hash': hash_password(demo_pass)},
    )
    db.add(demo)
    await db.flush()

    db.add(
        Membership(
            user_id=demo.id,
            tenant_id=tenant.id,
            role='admin',
            status='active',
        )
    )

    await db.commit()

    write_owner_account_file(email=owner_email, password=owner_pass)

    cred_path = _PROJECT_ROOT / '.tenderiq' / 'bootstrap-credentials.json'
    cred_path.parent.mkdir(parents=True, exist_ok=True)
    cred_path.write_text(
        json.dumps(
            {
                'note': 'Default dev accounts. System owner file: .tenderiq/owner-account.txt',
                'accounts': [
                    {'email': owner_email, 'password': owner_pass, 'role': 'platform_admin'},
                    {'email': demo_email, 'password': demo_pass, 'role': 'tenant_admin'},
                ],
            },
            indent=2,
        ),
        encoding='utf-8',
    )
    logger.info(
        'Bootstrap accounts created; owner login: %s',
        owner_account_file_path(),
    )
    return True
