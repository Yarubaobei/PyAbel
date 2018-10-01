# -*- coding: utf-8 -*-
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import os.path
import numpy as np
import abel
import glob

def get_bs_cached(method, cols, nbf, basis_dir='.', cached_basis=None,
                  basis_options=dict(), verbose=False):
    """load basis set from disk, generate and store if not available.

    Checks whether file ``{method}_basis_{cols}_{nbf}*.npy`` is present in 
    `basis_dir` 
    (*) special case for ``linbasex``
         _{legendre_orders}_{proj_angles}_{radial_step}_{clip} 
        where {legendre_orders} = str of the list elements, typically '02'
              (proj_angles} = str of the list elements, typically '04590135'
              {radial_step} = pixel grid size, usually 1
              {clip} = clipping size, usually 0

    Either, read basis array or generate basis, saving it to the file.
        

    Parameters
    ----------
    method : str
        Abel transform method, currently ``linbasex``, ``onion_peeling``,
        ``three_point``, and ``two_point``
    cols : int
        width of image
    nbf : int
        number of basis functions (usually = cols)
    basis_dir : str
        path to the directory for saving / loading the basis
    verbose: boolean
        print information for debugging 

    Returns
    -------
    D: numpy 2D array of shape (cols, nbf)
       basis operator array

    file.npy: file
       saves basis to file name ``{method}_basis_{cols}_{nbf}*.npy``
       * == ``__{legendre_orders}_{proj_angles}_{radial_step}_{clip}`` for 
       ``linbasex`` method

    """

    if cached_basis is not None and cached_basis[0] is not None:
        _basis, _method = cached_basis
        if _basis.shape[0] >= cols and _method == method:
            if verbose:
                print('Using memory cached basis')
            return _basis

    basis_generator = {
        "linbasex": abel.linbasex._bs_linbasex,
        "onion_peeling": abel.dasch._bs_onion_peeling,
        "three_point": abel.dasch._bs_three_point,
        "two_point": abel.dasch._bs_two_point
    }

    if method not in basis_generator.keys():
        raise ValueError("basis generating function for method '{}' not know"
                         .format(method))

    basis_name = "{}_basis_{}_{}".format(method, cols, nbf)
    # special case linbasex requires additional identifying parameters
    # 
    # linbasex_basis_cols_cols_02_090_0.npy
    if method == "linbasex": 
       # Fix Me! not a simple unique naming mechanism
        for key in ['legendre_orders', 'proj_angles', 'radial_step', 'clip']:
            if key in basis_options.keys():
                if key == 'legendre_orders':
                    value = ''.join(map(str, basis_options[key]))
                elif key == 'proj_angles':
                    # in radians, convert to % of pi
                    proj_angles_fractpi =\
                         np.array(basis_options['proj_angles'])*100/np.pi
                    
                    value = ''.join(map(str, proj_angles_fractpi.astype(int)))
                else: 
                    value = basis_options[key]
            else:
                # missing option, use defaults
                default = {'legendre_orders':'02', 'proj_angles':'050',
                           'radial_step':1, 'clip':0}
                value = default[key]

            basis_name += "_{}".format(value)

    basis_name += ".npy"

    D = None
    if basis_dir is not None:
        path_to_basis_files = os.path.join(basis_dir, method+'_basis*')
        basis_files = glob.glob(path_to_basis_files)
        for bf in basis_files:
            if int(bf.split('_')[-2]) >= cols:  # relies on file order
                if verbose:
                    print("Loading {:s} basis {:s}".format(method, bf))
                D = np.load(bf)
                # trim to size
                return D[:cols, :nbf] 

    if verbose:
        print("A suitable basis for '{}' was not found.\n"
              .format(method), 
              "A new basis will be generated.")
        if basis_dir is not None:
            print("But don\'t worry, it will be saved to disk for future",
                  " use.\n")
        else:
            pass

    D = basis_generator[method](cols, **basis_options)

    if basis_dir is not None:
        path_to_basis_file = os.path.join(basis_dir, basis_name)
        np.save(path_to_basis_file, D)
        if verbose:
            print("Operator matrix saved for later use to,")
            print(' '*10 + '{}'.format(path_to_basis_file))

    return D
