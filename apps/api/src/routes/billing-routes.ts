import { FastifyInstance, FastifyRequest, FastifyReply } from 'fastify';

interface PlanRoutesOptions {
  billingService: any;
}

export async function planRoutes(fastify: FastifyInstance, options: PlanRoutesOptions) {
  const { billingService } = options;

  fastify.get('/plans', async (request: FastifyRequest, reply: FastifyReply) => {
    try {
      const plans = await billingService.getPlans();
      return reply.send({ plans });
    } catch (error) {
      fastify.log.error(error);
      return reply.status(500).send({ error: 'Failed to fetch plans' });
    }
  });

  fastify.get('/subscription', async (request: FastifyRequest, reply: FastifyReply) => {
    try {
      const userId = (request as any).userId;
      const subscription = await billingService.getSubscription(userId);
      return reply.send({ subscription });
    } catch (error) {
      fastify.log.error(error);
      return reply.status(500).send({ error: 'Failed to fetch subscription' });
    }
  });

  fastify.post('/subscription', async (request: FastifyRequest, reply: FastifyReply) => {
    try {
      const userId = (request as any).userId;
      const { planId, billingInterval, paymentMethodId } = request.body as any;
      
      const subscription = await billingService.createSubscription(
        userId,
        planId,
        billingInterval,
        paymentMethodId
      );
      
      return reply.status(201).send({ subscription });
    } catch (error) {
      fastify.log.error(error);
      return reply.status(500).send({ error: 'Failed to create subscription' });
    }
  });

  fastify.patch('/subscription/:planId', async (request: FastifyRequest, reply: FastifyReply) => {
    try {
      const userId = (request as any).userId;
      const { planId } = request.params as any;
      const { billingInterval } = request.body as any;
      
      const result = await billingService.changePlan(userId, planId, billingInterval);
      return reply.send(result);
    } catch (error) {
      fastify.log.error(error);
      return reply.status(500).send({ error: 'Failed to change plan' });
    }
  });

  fastify.delete('/subscription', async (request: FastifyRequest, reply: FastifyReply) => {
    try {
      const userId = (request as any).userId;
      const { reason } = request.body as any || {};
      
      await billingService.cancelSubscription(userId, reason);
      return reply.send({ success: true });
    } catch (error) {
      fastify.log.error(error);
      return reply.status(500).send({ error: 'Failed to cancel subscription' });
    }
  });

  fastify.post('/subscription/reactivate', async (request: FastifyRequest, reply: FastifyReply) => {
    try {
      const userId = (request as any).userId;
      await billingService.reactivateSubscription(userId);
      return reply.send({ success: true });
    } catch (error) {
      fastify.log.error(error);
      return reply.status(500).send({ error: 'Failed to reactivate subscription' });
    }
  });

  fastify.get('/invoices', async (request: FastifyRequest, reply: FastifyReply) => {
    try {
      const userId = (request as any).userId;
      const invoices = await billingService.getInvoices(userId);
      return reply.send({ invoices });
    } catch (error) {
      fastify.log.error(error);
      return reply.status(500).send({ error: 'Failed to fetch invoices' });
    }
  });

  fastify.get('/invoices/:invoiceId', async (request: FastifyRequest, reply: FastifyReply) => {
    try {
      const userId = (request as any).userId;
      const { invoiceId } = request.params as any;
      
      const invoice = await billingService.getInvoice(userId, invoiceId);
      return reply.send({ invoice });
    } catch (error) {
      fastify.log.error(error);
      return reply.status(404).send({ error: 'Invoice not found' });
    }
  });

  fastify.get('/quota', async (request: FastifyRequest, reply: FastifyReply) => {
    try {
      const userId = (request as any).userId;
      const quota = await billingService.getQuotaStatus(userId);
      return reply.send({ quota });
    } catch (error) {
      fastify.log.error(error);
      return reply.status(500).send({ error: 'Failed to fetch quota status' });
    }
  });

  fastify.post('/quota/check', async (request: FastifyRequest, reply: FastifyReply) => {
    try {
      const userId = (request as any).userId;
      const { featureKey, amount } = request.body as any;
      
      const result = await billingService.checkQuota(userId, featureKey, amount);
      return reply.send(result);
    } catch (error) {
      fastify.log.error(error);
      return reply.status(500).send({ error: 'Failed to check quota' });
    }
  });

  fastify.get('/payment-methods', async (request: FastifyRequest, reply: FastifyReply) => {
    try {
      const userId = (request as any).userId;
      const methods = await billingService.getPaymentMethods(userId);
      return reply.send({ paymentMethods: methods });
    } catch (error) {
      fastify.log.error(error);
      return reply.status(500).send({ error: 'Failed to fetch payment methods' });
    }
  });

  fastify.post('/payment-methods', async (request: FastifyRequest, reply: FastifyReply) => {
    try {
      const userId = (request as any).userId;
      const { stripePaymentMethodId } = request.body as any;
      
      const method = await billingService.addPaymentMethod(userId, stripePaymentMethodId);
      return reply.status(201).send({ paymentMethod: method });
    } catch (error) {
      fastify.log.error(error);
      return reply.status(500).send({ error: 'Failed to add payment method' });
    }
  });

  fastify.delete('/payment-methods/:methodId', async (request: FastifyRequest, reply: FastifyReply) => {
    try {
      const userId = (request as any).userId;
      const { methodId } = request.params as any;
      
      await billingService.removePaymentMethod(userId, methodId);
      return reply.send({ success: true });
    } catch (error) {
      fastify.log.error(error);
      return reply.status(500).send({ error: 'Failed to remove payment method' });
    }
  });

  fastify.patch('/payment-methods/:methodId/default', async (request: FastifyRequest, reply: FastifyReply) => {
    try {
      const userId = (request as any).userId;
      const { methodId } = request.params as any;
      
      await billingService.setDefaultPaymentMethod(userId, methodId);
      return reply.send({ success: true });
    } catch (error) {
      fastify.log.error(error);
      return reply.status(500).send({ error: 'Failed to update payment method' });
    }
  });

  fastify.get('/portal', async (request: FastifyRequest, reply: FastifyReply) => {
    try {
      const userId = (request as any).userId;
      const { url, expiresAt } = await billingService.createBillingPortalSession(userId);
      return reply.send({ url, expiresAt });
    } catch (error) {
      fastify.log.error(error);
      return reply.status(500).send({ error: 'Failed to create portal session' });
    }
  });
}

export default planRoutes;