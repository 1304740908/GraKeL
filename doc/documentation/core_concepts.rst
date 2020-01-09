.. _core_concepts:

=============
Core Concepts
=============

We next present some core concepts in *GraKeL*.

What is the :class:`grakel.GraphKernel` Class?
---------------------------------------
The :class:`grakel.GraphKernel` class is a *generic wrapper class*. This class provides a uniform interface for all the implemented graph kernels and frameworks. A graph kernel can be described by an instance of this class, and it holds the attributes listed below:

* :code:`kernel` : Specifies the graph kernel to be computed. It can be either a :code:`base_graph_kernel` or a list that contains one or more :code:`framework` along with exactly one :code:`base_graph_kernel`. The :code:`base_graph_kernel` needs to be the last element in the list.
    - :code:`base_graph_kernel` : Α :code:`base_graph_kernel` is a kernel that compares graphs to each other. It is represented by a dictionary which contains a key :code:`'name'` whose value  corresponds to the name of the kernel. The dictionary can also contain other keys that specify the parameters of the kernel and their values. For instance, we can initialize a shortest path kernel as follows.

    .. code-block:: python

        >>> from grakel import GraphKernel
        >>> gk = GraphKernel(kernel={"name": "shortest_path", "with_labels": False})

    - :code:`framework` : A :code:`framework` works on top of graph kernels. It takes a :code:`base_graph_kernel` as input. Frameworks correspond to dictionaries that contain their name as the value of the key :code:`'name'`, and their parameters. A :code:`framework` combined with a :code:`base_graph_kernel` corresponds to a :code:`base_graph_kernel` and can be passed on to another :code:`framework`. For example, a kernel that applies the Weisfeiler-Lehman framework on top of the shortest path kernel is initialized as follows.

    .. code-block:: python

        >>> from grakel import GraphKernel
        >>> gk = GraphKernel(kernel=[{"name": "weisfeiler_lehman", "n_iter": 5}, {"name": "shortest_path"}])

* :code:`normalize` : A kernel can provide either an unnormalized or a normalized output.
    The normalized kernel value between two graphs :math:`G_1` and :math:`G_2` is computed as follows: :math:`k(G_1, G_2)/\sqrt{k(G_1, G_1) k(G_2, G_2)}`. This normalization ensures that the kernel value between a graph and itself is equal to 1, while the kernel value between a graph and any other graph takes values between 0 and 1.

    | **Example**
    
    Suppose we have a set of training graphs :code:`G_train`, and a set of test graphs :code:`G_test`. We compute the normalized kernel matrices using the Weisfeiler-Lehman subtree kernel as follows.

    .. code-block:: python

        >>> gk = GraphKernel(kernel=[{"name": "weisfeiler_lehman", "n_iter": 5}, {"name": "subtree_wl"}], normalize=True)
        >>> # Calculate the normalized kernel matrices
        >>> K_train = gk.fit_transform(G_train)
        >>> K_test = gk.transform(G_test)

    The above is equivalent (for deterministic kernels) to the code below.

    .. code-block:: python

        >>> gk = GraphKernel(kernel=[{"name": "weisfeiler_lehman", "n_iter": 5}, {"name": "subtree_wl"}], normalize=False)
        >>> K = gk.fit_transform(G)
        >>> K_diag = K.diagonal()
        >>> K_train_diag, K_test_diag = K_diag[idx_train], K_diag[idx_test]
        >>> # Calculate the normalized kernel matrices
        >>> K_train = K[idx_train, :][:, idx_train] / np.sqrt(np.outer(K_train_diag, K_train_diag))
        >>> K_test = K[idx_test, :][:, idx_train] / np.sqrt(np.outer(K_test_diag, K_train_diag))

    Note that in the second case, we perform more computations since we also compare the graphs of the test set to each other.

* :code:`Nystroem` : The Nyström method is a well-established approach for approximating kernel matrices on large datasets.
    If :math:`n` is the number of samples, computing and storing the kernel matrix requires :math:`\mathcal{O}(n^2)` time and memory, respectively. Therefore, applying kernel methods will become unfeasible when :math:`n` is large. The Nyström approximation can allow a significant speed-up of the calculations by computing an approximation :math:`\tilde{\mathbf{K}}` of rank :math:`q` of the kernel matrix. The method uses a subset of the training data as basis and reduces the storage and complexity requirements to :math:`\mathcal{O}(n q)`. The value of :math:`q` is specified by the user by setting :code:`Nystroem` equal to an integer value. An example demonstrating the power of the Nyström method is given below.

    | **Example**

    We first download the MUTAG dataset and split it into a training and a test set.

    .. doctest:: 

        >>> from grakel.datasets import fetch_dataset
        >>> from sklearn.model_selection import train_test_split
        >>> MUTAG = fetch_dataset("MUTAG", verbose=False)
        >>> G = MUTAG.data
        >>> y = MUTAG.target
        >>> G_train, G_test, y_train, y_test = train_test_split(G, y, test_size=0.1)

    We next initialize a Weisfeiler-Lehman subtree kernel using :code:`GraphKernel`, and we also make use of :code:`Nystroem` with :math:`q=20` to approximate the kernel matrix.

    .. doctest:: 

        >>> from grakel import GraphKernel
        >>> gk = GraphKernel(kernel=[{"name": "weisfeiler_lehman", "n_iter": 5}, "subtree_wl"], Nystroem=20)
        >>> K_train = gk.fit_transform(G_train)
        >>> K_test = gk.transform(G_test)
        >>> print(K_train.shape)
        (169, 20)
        >>> print(K_test.shape)
        (19, 20)

    Then, we train a standard SVM classifier with linear kernel, and use the classifier to make predictions.

    .. doctest:: 

        >>> from sklearn.svm import SVC
        >>> clf = SVC(kernel='linear')
        >>> clf.fit(K_train, y_train)
        SVC(C=1.0, break_ties=False, cache_size=200, class_weight=None, coef0=0.0,
            decision_function_shape='ovr', degree=3, gamma='scale', kernel='linear',
            max_iter=-1, probability=False, random_state=None, shrinking=True,
            tol=0.001, verbose=False)
        >>> y_pred = clf.predict(K_test)

    Finally, we calculate the classification accuracy.

    .. doctest::

        >>> from sklearn.metrics import accuracy_score
        >>> print(str(round(accuracy_score(y_test, y_pred)*100, 2)), "%")
        78.95 %

    .. note::
        | To compute the full kernel matrices, we needed to perform :math:`~ 169 * (169-1) /2 + 19 * 169 = 17,407` kernel computations. Instead, we performed :math:`~ 20 * (20-1)/ 2 + 20 * 169 + 20* 19 = 3,950` kernel computations. As we can see, the approximation led only to a slight decrease in performance.

* :code:`n_jobs` : Some kernels consist of operations that can be executed in parallel, leading to a reduction in the running time.
    The :code:`n_jobs` attribute has the same functionality as that of scikit-learn. It determines the number of jobs that will run in parallel. If :code:`n_jobs` is set equal to -1, all the processors will be utilized. Note that this attribute will not have an impact on the computation of some kernels whose code is not parallelized. These kernels either take advantage of the parallelization inherent in other libraries (e.g., NumPy) or their code is only partially parallelizable or not parallelizable at all. In such scenarios, a warning is issued.

    If you are interested in parallelizing any of the implemented kernels, you can *contribute* to the *GraKeL* project. To find out how you can contribute, please have a look at :ref:`contributing`.

* :code:`random_state` : This attribute is used for initializing the internal random number generator.
    It has no effect on deterministic graph kernels, but only on kernels that involve some random process (e.g., those that perform sampling). It also applies to the :code:`Nystroem` function of the :code:`GraphKernel` class which also performs sampling. If int, :code:`random_state` is the seed used by the random number generator. Otherwise, it can be a :code:`RandomState` instance. If :code:`None`, the random number generator is the :code:`RandomState` instance used by :code:`np.random`. The use of :code:`random_state` is illustrated in the following example.

    | **Example**

    We first create the graph representations of the following two molecules: (1) water :math:`\mathbf{H}_{2}\mathbf{O}` and (2) hydronium :math:`\mathbf{H}_{3}\mathbf{O}^{+}`, an ion of water produced by protonation.

    .. code-block:: python

       >>> from grakel import Graph
       >>>
       >>> H2O_adjacency = [[0, 1, 1], [1, 0, 0], [1, 0, 0]]
       >>> H2O_node_labels = {0: 'O', 1: 'H', 2: 'H'}
       >>> H2O = Graph(initialization_object=H2O_adjacency, node_labels=H2O_node_labels)
       >>>
       >>> H3O_adjacency = [[0, 1, 1, 1], [1, 0, 0, 0], [1, 0, 0, 0], [1, 0, 0, 0]]
       >>> H3O_node_labels = {0: 'O', 1: 'H', 2: 'H', 3:'H'}
       >>> H3O = Graph(initialization_object=H3O_adjacency, node_labels=H3O_node_labels)

    We will then compute the *graphlet kernel* between the two molecules. The graphlet kernel counts the number of common graphlets (i.e., small subgraphs) in two graphs. Instead of exaustively enumerating all the graphlets, it usually samples a number of them. In this example, we will sample 5 graphlets from each graph.

    .. doctest::

        >>> gk = GraphKernel(kernel=dict(name="graphlet_sampling", sampling=dict(n_samples=5)))
        >>> gk.fit(H2O)
        GraphKernel(Nystroem=False,
              kernel={'name': 'graphlet_sampling', 'sampling': {'n_samples': 5}},
              n_jobs=None, normalize=False, random_state=None, verbose=False)
    
        >>> gk.transform(H3O)
        array([[10.]])

    Note that we did not set :code:`random_state` to some value, and therefore it took its default :code:`None` value. We will now set :code:`random_state` equal to 42.

    .. doctest:: 

        >>> gk = GraphKernel(kernel=dict(name="graphlet_sampling", sampling=dict(n_samples=5), random_state=42))
        >>> gk.fit(H2O)
        GraphKernel(Nystroem=False,
              kernel={'name': 'graphlet_sampling', 'sampling': {'n_samples': 5}, 'random_state': 42},
              n_jobs=None, normalize=False, random_state=None, verbose=False)

        >>> gk.transform(H3O)
        array([[15.]])

    As you can see, the new kernel value is not equal to the previous one. If we re-run the above code, we will obtain the same kernel value since the algorithm will sample exactly the same graphlets from both graphs. As shown below, we can also obtain the same kernel value if :code:`random_state` is initialized as an attribute of :code:`GraphKernel` instead of the graphlet kernel itself.

    .. doctest::

        >>> gk = GraphKernel(kernel=dict(name="graphlet_sampling", sampling=dict(n_samples=5)), random_state=42)
        >>> gk.fit(H2O)
        GraphKernel(Nystroem=False,
              kernel={'name': 'graphlet_sampling', 'sampling': {'n_samples': 5}},
              n_jobs=None, normalize=False, random_state=42, verbose=False)
    
        >>> gk.transform(H3O)
        array([[15.]])

    If we provide a :code:`random_state` value to both :code:`GraphKernel` and :code:`kernel`, then each one will have an effect only on the corresponding instances.

    .. doctest::

        >>> gk = GraphKernel(kernel=dict(name="graphlet_sampling", sampling=dict(n_samples=5, random_state=0)), random_state=42)
        >>> gk.fit(H2O)
        GraphKernel(Nystroem=False,
              kernel={'name': 'graphlet_sampling', 'sampling': {'n_samples': 5, 'random_state': 0}},
              n_jobs=None, normalize=False, random_state=42, verbose=False)
    
        >>> gk.transform(H3O)
        array([[15.]])

    while

    .. doctest::

        >>> gk = GraphKernel(kernel=dict(name="graphlet_sampling", sampling=dict(n_samples=5)), random_state=0)
        >>> gk.fit(H2O).transform(H3O)
        array([[10.]])


* :code:`verbose` : Currently not supported.
    .. note::
        :code:`verbose` is an attribute that is currently not supported, but may be supported in the future for printing progress messages.

We will next focus on the :class:`grakel.Kernel` class. Instances of this class are wrapped in an instance of the :class:`grakel.GraphKernel` class that was presented above.

The `Kernel` class
------------------
This :code:`Object` is any object inherited from the :ref:`kernel` (which can be imported from :code:`grakel`).

Normally a kernel function, between graphs should be considered as a function with to arguments,
such as :math:`k \; : \; \mathcal{G} \times \mathcal{G} \rightarrow \mathbb{R}`.
This raises two issues, namely one of efficiency and one of compatibility:

1. The first one has to do with the fact, that there are major computational advantages if instead of calculating the kernel pairwise, we calculate the whole kernel matrix.

2. The second has to do with the fact, that we wanted our project to be integrable inside the `sk learn template`_. From this template the most relevant structure was the sci-kit transformer, which consists of three inherent methods: :code:`fit`, :code:`fit_transform`, :code:`transform`.

So the way we conceptually attached the kernel definition to that design pattern was:

- The :code:`fit` part should fix a graph dataset as the base of comparison calculating necessary features.

- The :code:`fit_transform` should fit and calculate the kernel matrix on the fitted dataset.

- The :code:`transform` should calculate the matrix produced between a new dataset (namely the *test*) and the fitted dataset.

The deconstruction of the kernel matrix calculation from a function :math:`\mathcal{K}: \mathcal{G}^{\text{train}} \times \mathcal{G}^{\text{test}} \rightarrow \mathbb{R}^{n_{\text{test}}} \times \mathbb{R}^{n_{\text{train}}}`
to a `currying`_ scheme :math:`\mathcal{K}: \mathcal{G}^{\text{train}} \rightarrow \mathcal{G}^{\text{test}} \rightarrow \mathbb{R}^{n_{\text{test}}} \times \mathbb{R}^{n_{\text{train}}}` is not always equivalent in the
result, if some of the data of :math:`\mathcal{G}^{\text{train}}`, must be combined with data of :math:`\mathcal{G}^{\text{test}}` to produce the fit reference-features. In such cases
as mentioned above, namely in the case of :code:`multiscale_laplacian`, if the user wants :math:`\mathcal{G}^{\text{train}} \rightarrow \mathcal{G}^{\text{test}}` to be concerned
before fit we advise him to use the :code:`fit_transform`, function in the whole of the train and test data and separate the kernel matrices on the result.

.. note::
    The very idea that lies before fitting concerns holding a reference dataset. This means a collections of features should be stored into memory and **not** get corrupted throughout various applications of :code:`transform`. This however - the need of copying and protecting the reference data - produces a computational overhead in kernels such as the :code:`odd_sth` where the user will may prefer the computational advantages of applying a sole :code:`fit_transform`.

Using a :code:`Kernel` type object through the generic wrapper, should be equivalent with doing so without the generic wrapper, if the correct parametrization is given.
The generic wrapper **does not** restrict any *user-oriented* interface of the kernels, except if the user wants to write a kernel of his own.
If you want to know more about the kernel structure in order to write your own see :ref:`myok`.

To demonstrate a small example of the above we will construct our own a WL-subtree kernel instead of using the generic wrapper.
To do so first import the :code:`WeisfeilerLehman` and :code:`VertexHistogram` (where :code:`vertex_histogram` is equivalent
with the :code:`subtree_kernel`) kernels as

.. code-block:: python

    >>> from grakel import WeisfeilerLehman
    >>> from grakel import VertexHistogram

If we see the documentation of :ref:`weisfeiler_lehman`, we can see that it accepts two arguments upon initialization: a :code:`niter` and a :code:`base_graph_kernel`. The :code:`base_graph_kernel` is a tuple consisting of a :code:`kernel` type object and a dictionary of arguments. To initialize a Weisfeiler-Lehman with 5 iterations and a subtree base-kernel.

.. code-block:: python

    >>> wl_kernel = WeisfeilerLehman(niter=5, base_graph_kernel=(VertexHistogram, {}))

This is also equivalent with doing (as long as we have no arguments)

.. code-block:: python

    >>> wl_kernel = WeisfeilerLehman(niter=5, base_graph_kernel=VertexHistogram)

Now let's go back again to our favorite MUTAG problem.

.. code-block:: python

    >>> from grakel import datasets
    >>> MUTAG = datasets.fetch_dataset("MUTAG", verbose=False)
    >>> MUTAG_data, y = MUTAG.data, MUTAG.target
    >>> split_point = int(len(MUTAG_data) * 0.9)
    >>> X, Y = MUTAG_data[:split_point], MUTAG_data[split_point:]

If what we said till now is correct, the :code:`GraphKernel` object should produce the same kernel matrix output on the MUTAG train/test data split.

.. code-block:: python

    >>> from grakel import GraphKernel
    >>> wl_graph_kernel = GraphKernel(kernel = [{"name": "weisfeiler_lehman", "niter": 5}, {"name": "subtree_wl"}])
    >>> # The alias "subtree_wl" is supported inside the generic wrapper
    >>> from numpy import array_equal
    >>> array_equal(wl_graph_kernel.fit_transform(X), wl_kernel.fit_transform(X))
    True
    >>> array_equal(wl_graph_kernel.transform(Y), wl_kernel.transform(Y))
    True

.. _currying: https://en.wikipedia.org/wiki/Currying
.. _sk learn template: https://github.com/scikit-learn-contrib/project-template

Why not a more structured input for Graphs?
-------------------------------------------
The flattened input type provided for all kernels (graph-dictionary/adjacency, node-labels, edge-labels) may raise the question,
why does not this library, accept a well known type of Graph input as the one constructed from `networkx`_ or `igraph`_.
Networkx library is known for producing a very big memory overhead, which seems unimportant when the user wants to use
very basic graph methods such calculating shortest paths or getting a vertex neighbor. Because what we wanted to wrap
around a graph class was really simple: conversion between dictionary and adjacency formats, format agnostic - format imposing
methods and very basic graph oriented supplementary methods, such as *Shortest-Path matrix* calculation, we designed
a Graph class of our own, used inside most of our kernels, in order to resolve to a common object - graph format reference.
This specificity of kernel format, as well as the absence of a need for complex calculations concerning the field of graphs
lead us to the creation of :ref:`Graph`.

Let's go back to the H2O example:
First we will import the :code:`Graph` object from :code:`Grakel`

.. code-block:: python

    >>> from grakel import Graph

Firstly let's collect all the dictionary formats and show that they are equivalent.
We start by calculating a graph object for the native format of graph dictionary which corresponds to the following:

.. code-block:: python

    >>> H2Od = dict()
    >>> H2Od[0] = {'a': {'b': 1., 'c': 1.}, 'b': {'a': 1}, 'c': {'a': 1}}

Now let's initialize all the other

.. code-block:: python

    >>> H2Od[1] = {'a': ['b', 'c'], 'b': ['a'], 'c':['b']}
    >>> H2Od[2] = {('a', 'b'): 1., ('a', 'c'): 1., ('c', 'a'): 1., ('b', 'a'): 1.}
    >>> H2Od[3] = [('a', 'b'), ('a', 'c'), ('b', 'a'), ('c', 'a')]
    >>> H2Od[4] = [('a', 'b', 1.), ('a', 'c', 1.), ('b', 'a', 1.), ('c', 'a', 1.)]

and compute the result

.. code-block:: python

    >>> any(Graph(H2Od[i]).get_edge_dictionary() == H2Od[0] for i in range(1, 5))
    True

Now let's do the same for adjacency matrix type formats. The numpy array is the native adjacency-matrix format:

.. code-block:: python

    >>> from numpy import array
    >>> H2O = dict()
    >>> H2O[0] = array([[0, 1, 1], [1, 0, 0], [1, 0, 0]])

and with the conversion of other input type formats

.. code-block:: python

    >>> H2O[1] = [[0, 1, 1], [1, 0, 0], [1, 0, 0]]
    >>> from scipy.sparse import csr_matrix
    >>> H2O[2] = csr_matrix(([1, 1, 1, 1], ([0, 0, 1, 2], [1, 2, 0, 0])), shape=(3, 3))

we can demonstrate equality as

.. code-block:: python

    >>> from numpy import array_equal
    >>> all(array_equal(Graph(H2O[i]).get_adjacency_matrix(), H2O[0]) for i in range(1, 3))
    True

Now we would like to initialize two :code:`Graph` type objects one for adjacency_matrix and one for edge_dictionary and show that they are equivalent (using also labels).
First initialize the graph object, created from an adjacency matrix:

.. code-block:: python

    >>> H2O_labels = {0: 'O', 1: 'H', 2: 'H'}
    >>> H2O_edge_labels = {(0, 1): 'pcb', (1, 0): 'pcb', (0, 2): 'pcb', (2, 0): 'pcb'}
    >>> adj_graph = Graph(H2O[0], H2O_labels, H2O_edge_labels, "all")

and one from an edge dictionary:

.. code-block:: python

    >>> H2Od_labels = {'a': 'O', 'b': 'H', 'c': 'H'}
    >>> H2Od_edge_labels = {('a', 'b'): 'pcb', ('b', 'a'): 'pcb', ('a', 'c'): 'pcb', ('c', 'a'): 'pcb'}
    >>> edge_dict_graph = Graph(H2Od[0], H2Od_labels, H2Od_edge_labels, "all")

Firstly we will demonstrate equality of graph type formats:

.. code-block:: python

    >>> array_equal(adj_graph.get_adjacency_matrix(), edge_dict_graph.get_adjacency_matrix())
    True

and

.. code-block:: python

    >>> adj_graph.get_edge_dictionary() == edge_dict_graph.get_edge_dictionary()
    True

and afterwards between labels for :code:`"adjacency"` object formats, defined by the :code:`purpose` argument of the :code:`get_labels` method from the :code:`Graph` type object and for both vertices or edges defined by the :code:`label_type` format of the same method, as

.. code-block:: python

    >>> all((adj_graph.get_labels(purpose="adjacency", label_type=lt), edge_dict_graph.get_labels(purpose="adjacency", label_type=lt)) for lt in ["vertex", "edge"])
    True

Checking equality of the inverse ("edge_dictionary") want hold, because the adjacency matrix, when initialized does not have information about the vertex symbols.
Here we should emphasize that **vertex symbols should be a :code:`sortable` in order for an indexing to be possible**.

.. note::
    When initializing a :code:`Graph` object the 4th argument (named :code:`graph_format`), corresponds to the format the :code:`Graph` will be stored to. The default value of this argument is :code:`"auto"`, which stores the graph in the given format, if it is valid. Explicit format "choices" such as :code:`"adjacency"` or :code:`"dictionary"`, will (covert if needed and) store the :code:`Graph` in this format type. By initializing the :code:`Graph` format as all in the above example, we simply make sure that the :code:`Graph` instance will contain both adjacency and dictionary graph representations and their corresponding edge and adjacency labels for both nodes and edges. Although the methods :code:`get_adjacency_matrix` and `get_edge_dictionary`, construct and return such a graph representation if non existent, the :code:`get_labels` method will change the graph format if the requested labels are not in the desired format and pop a certain warning. If the user wants to avoid doing so he can either set the explicit format afterwards by executing

    .. code-block:: python

        >>> adj_graph = Graph(H2O[0], H2O_labels, H2O_edge_labels)
        >>> adj_graph.set_format("all")

    or declare which is the desired format format he wants the graph to support and it will be included automatically by executing

    .. code-block:: python

        >>> adj_graph.desired_format("dictionary")

    which in that case will set the :code:`Graph` instance format from :code:`"adjacency"` to :code:`"all"`, in order to include the specified format.

After this long introduction of what the :code:`Graph` Object is, the way this can interest the user is by utilizing as input for :code:`GraphKernel`.
Because this Object will act as a mutable-object, any necessary format conversion inside a dataset will happen only ones and the user can execute
multiple kernels on a single dataset with repeating conversions again and again. An important thing to mention here is that a kernel Object **should
not** cause information loss concerning a the :code:`Graph` data Object given as input.

Now let's demonstrate the simple water example on a Shortest-Path kernel, using :code:`Graph` type objects.
First initialize those objects:

.. code-block:: python

    >>> H2O = Graph([[0, 1, 1], [1, 0, 0], [1, 0, 0]], {0: 'O', 1: 'H', 2: 'H'})
    >>> H3O = Graph([[0, 1, 1, 1], [1, 0, 0, 0], [1, 0, 0, 0], [1, 0, 0, 0]], {0: 'O', 1: 'H', 2: 'H', 3:'H'})

And calculate fit transform

.. code-block:: python

    >>> from grakel import GraphKernel
    >>> sp_kernel = GraphKernel(kernel = {"name": "shortest_path"}, normalize=True)
    >>> sp_kernel.fit_transform([H2O])
    1.0

and finally the normalized kernel value, between :math:`\mathbf{H}_{2}\mathbf{O}` and :math:`\mathbf{H}_{3}\mathbf{O}^{+}`

.. code-block:: python

    >>> sp_kernel.transform([H3O])
    0.9428090415820634

which is equivalent with the originally computation, we did on introduction.

.. _networkx: https://networkx.github.io/
.. _igraph: http://igraph.org/python/
