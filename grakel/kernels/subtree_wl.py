"""This file contains the subtree kernel, used by default in wl."""
import collections
import warnings

from grakel.graph import Graph
from grakel.tools import inv_dict

from grakel.kernels import kernel


class subtree_wl(kernel):
    r"""The weisfeiler lehman subtree kernel.

    See :cite:`Shervashidze2011WeisfeilerLehmanGK`.

    The kernel value.

    .. math::
        k(X,Y) = \sum_{v \in V_{1}}\sum_{u \in V_{2}}\delta(l(v),l(u))

    Parameters
    ----------
    None.

    Attributes
    ----------
    X : dict
        Inverse dictionaries of labels for the input.

    """

    _graph_format = "auto"

    def __init__(self, **kargs):
        """Initialise a subtree_wl kernel."""
        super(subtree_wl, self).__init__(**kargs)

    def parse_input(self, X):
        """Parse and check the given input for dirac kernel.

        Parameters
        ----------
        X : iterable
            For the input to pass the test, we must have:
            Each element must be an iterable with at most three features and at
            least one. The first that is obligatory is a valid graph structure
            (adjacency matrix or edge_dictionary) while the second is
            node_labels and the third edge_labels (that correspond to the given
            graph format). A valid input also consists of graph type objects.

        Returns
        -------
        Xp : list
            List of graph type objects.

        """
        if not isinstance(X, collections.Iterable):
            raise ValueError('input must be an iterable\n')
        else:
            Xp = list()
            for (i, x) in enumerate(iter(X)):
                is_iter = isinstance(x, collections.Iterable)
                if is_iter:
                    x = list(x)
                if is_iter and len(x) in [0, 2, 3]:
                    if len(x) == 0:
                        warnings.warn('Ignoring empty element' +
                                      ' on index: '+str(i))
                        continue
                    else:
                        invL = inv_dict(x[1])
                elif type(x) is Graph:
                    invL = inv_dict(x.get_labels(purpose="any"))
                else:
                    raise ValueError('each element of X must be either a ' +
                                     'graph object or a list with at least ' +
                                     'a graph like object and node labels ' +
                                     'dict \n')
                Xp.append(invL)
            if len(Xp) == 0:
                raise ValueError('parsed input is empty')
            return Xp

    def pairwise_operation(self, lx, ly):
        """Calculate the kernel value between two elements.

        Parameters
        ----------
        l{x, y}: dict
            Inverse label dictionaries.

        Returns
        -------
        kernel : number
            The kernel value.

        """
        if len(lx) < len(ly):
            ls, lb = lx, ly
        else:
            ls, lb = ly, lx
        return sum(len(ls[x])*len(lb[x]) for x in ls if x in lb)
