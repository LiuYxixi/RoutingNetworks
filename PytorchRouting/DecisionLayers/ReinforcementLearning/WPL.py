"""
This file defines class REINFORCE.

@author: Clemens Rosenbaum :: cgbr@cs.umass.edu
@created: 6/7/18
"""
import copy
import torch
import torch.nn.functional as F

from ..Decision import Decision


class WPL(Decision):
    """
    Weighted Policy Learner (WPL) Multi-Agent Reinforcement Learning based decision making.
    """

    def _construct_policy_storage(self, *args, **kwargs):
        Decision._construct_policy_storage(self, *args, **kwargs)
        self._value_mem = copy.deepcopy(self._policy)

    @staticmethod
    def _loss(sample):
        grad_est = sample.state[:, 1, sample.action] - sample.cum_return
        grad_projected = torch.where(grad_est < 0, 1. + grad_est, 2. - grad_est)
        prob_taken = sample.state[:, 0, sample.action]
        act_loss = F.smooth_l1_loss(prob_taken, (prob_taken * grad_projected).data)
        ret_loss = F.smooth_l1_loss(sample.state[:, 1, sample.action], sample.cum_return.reshape(-1)).unsqueeze(-1)
        return act_loss + ret_loss

    def _forward(self, xs, mxs, agent):
        policy = self._policy[agent](xs)
        # policy = F.relu(policy) - F.relu(policy - 1.) + 1e-6
        policy = policy - policy.min(dim=1)[0] + 1e-6
        policy = policy/policy.sum(dim=1)
        values = self._value_mem[agent](xs)
        distribution = torch.distributions.Categorical(probs=policy)
        actions = distribution.sample()
        state = torch.stack([distribution.logits, values], 1)
        return xs, actions, state