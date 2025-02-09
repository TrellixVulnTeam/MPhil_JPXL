
"""GigaAnalysis - Data Type

This holds the data class and the functions that will manipulate them.

"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.interpolate import interp1d
from scipy.signal import savgol_filter, get_window, find_peaks

def _pick_float_dtype(to_check):
    """Return np.complex128 for complex dtypes, np.float64 otherwise.
    Adapted from scipy.interpolate"""
    if isinstance(to_check, np.ndarray):
        dtype = to_check.dtype
    else:
        dtype = type(to_check)
    if np.issubdtype(dtype, np.complexfloating):
        return np.complex_
    else:
        return np.float_


def _as_float_array(x):
    """Convert the input into a C contiguous float array.
    Adapted from scipy.interpolate
    NB: Upcasts half- and single-precision floats to double precision.
    """
    x = np.ascontiguousarray(x)
    x = x.astype(_pick_float_dtype(x), copy=False)
    return x


class Data():
    """
    The Data Class

    Data object holds the data in the measurements. It works as a simple
    wrapper of a two column numpy array (:class:`numpy.ndarray`). The data 
    stored in the object is meant to be interpreted as x is a independent 
    variable and y is dependant variable.


    Parameters
    ----------
    values : numpy.ndarray 
        A two column numpy array with the x data in the first column and 
        the y data in the second. If a second no array is given then the 
        first corresponds to the x data.
    split_y : numpy.ndarray, optional
        A 1D numpy array containing the y data. If None all the data 
        should be contained in first array.
    strip_sort : bool or {'strip', 'sort'}, optional
        If true the data points with NaN are removed using 
        :func:`numpy.isfinite` and the data is sorted by the x values.
        If 'strip' is given NaNs are removed but the data isn't sorted.
        If 'sort' is given the data is sorted but NaNs are left in.
        Default is False so the data isn't changed.
    interp_full : float, optional
        This interpolates the data to give an even spacing using the 
        inbuilt method :meth:`to_even`. The default is None and the 
        interpolation isn't done.

    Attributes
    ----------
    values : numpy.ndarray
        Two column numpy array with the x and y data in.
    x : numpy.ndarray
        x data in a 1D numpy array.
    y : numpy.ndarray
        The y data in a 1D numpy array.
    both : (numpy.ndarray, numpy.ndarray)
        A two value tuple with the :attr:`x` and :attr:`y` in.

    Notes
    -----
    Mathematical operations applied to the Data class just effects 
    the :attr:`y` values, the :attr:`x` values stay the same. To 
    act two :class:`Data` objects together the :attr:`x` values need to 
    agree. :class:`Data` objects also be mathematically acted to 
    array_like objects (:func:`numpy.asarray`) of length 1 or equal to the 
    length of the Data.

    """
    def __init__(self, values, split_y=None, strip_sort=False,
                 interp_full=None):
        if isinstance(values, Data):
            values = values.values  # If you pass a Data object to the class

        values = np.asarray(values)

        if split_y is not None:
            split_y = np.asarray(split_y)
            if values.ndim != 1:
                raise ValueError(
                    f"If x and y data are split both need to be a "
                    f"1D numpy array. values has shape {values.shape}")
            elif split_y.ndim != 1:
                raise ValueError(
                    f"If x and y data are split both need to be a "
                    f"1D numpy array. split_y has shape {split_y.shape}")
            elif values.size != split_y.size:
                raise ValueError(
                    f"If x and y data are split both need to be the same "
                    f"size. values has size {values.size} and split_y has "
                    f"size {split_y.szie}")
            values = np.concatenate(
                [values[:, None], split_y[:, None]], axis=1)

        if values.ndim != 2:
            raise ValueError(
                f"values needs to be a two column numpy array."
                f"values has the shape {values.shape}")
        elif values.shape[1] != 2:
            raise ValueError(
                f"values needs to be a two column numpy array."
                f"values has the shape {values.shape}")

        if strip_sort:
            if strip_sort == 'strip':
                values = values[np.isfinite(values).any(axis=1)]
            elif strip_sort == 'sort':
                values = values[np.argsort(values[:, 0]), :]
            else:
                values = values[np.isfinite(values).any(axis=1)]
                values = values[np.argsort(values[:, 0]), :]


        self.values = _as_float_array(values)   # All the data
        self.x = self.values[:, 0]  # The x data
        self.y = self.values[:, 1]  # The y data
        self.both = self.x, self.y  # Tuple of the data

        if interp_full:
            self.to_even(interp_full)


    def __str__(self):
        return np.array2string(self.values)

    def __repr__(self):
        return f"GA Data object:\n {str(self.values)[1:-1]}"

    def __dir__(self):
        return ['values', 'x', 'y', 'both',
                'y_from_x', 'x_cut',
                'interp_full', 'interp_number', 'interp_range',
                'plot']

    def __len__(self):
        return self.x.size

    def __bool__(self):
        if self.values.size == 0:
            return False
        else:
            return True

    def __maths_check(self, other, operation,):
        """This performs the error checking on the standard operators

        Parameters
        ----------
        other : :class:`Data` or array_like
            The feature that the data object maths acts on.
        operation : str
            The name of the operation being applied.

        Returns
        -------
            Array like object to calculate with
        """
        if isinstance(other, Data):
            if np.array_equal(self.x, other.x):
                return other.y
            else:
                raise ValueError(
                    f"The two Data classes do not have the same x "
                    f"values, so cannot be {operation}")
        try:
            other = np.asarray(other, dtype=_pick_float_dtype(other))
        except:
            raise TypeError(
                f"Data cannot be {operation} with object of "
                f"type {type(other)}.")
        if other.size == 1:
            return other
        elif other.ndim != 1:
            raise ValueError(
                f"Array to {operation} Data object with is of the wrong "
                f"dimension. Its shape is {other.shape}")
        elif other.size != self.x.size:
            raise ValueError(
                f"Array to {operation} Data object with is of the wrong "
                f"length. Its length is {other.size} while the Data "
                f"is {self.x.size}")
        else:
            return other

    def __mul__(self, other):
        """Multiplication of the y values. """
        other = self.__maths_check(other, "multiplied")
        return Data(self.x, self.y*other)
     
    def __rmul__(self, other):
        other = self.__maths_check(other, "multiplied")
        return Data(self.x, other*self.y)

    def __truediv__(self, other):
        """Division of the y values."""
        other = self.__maths_check(other, "divided")
        return Data(self.x, self.y/other)

    def __rtruediv__(self, other):
        other = self.__maths_check(other, "divide by")
        return Data(self.x, other/self.y)

    def __add__(self, other):
        """Addition of the y values."""
        other = self.__maths_check(other, "added")
        return Data(self.x, self.y + other)

    def __radd__(self, other):
        other = self.__maths_check(other, "added")
        return Data(self.x, other + self.y)

    def __sub__(self, other):
        """Subtraction of the y values."""
        other = self.__maths_check(other, "subtracted")
        return Data(self.x, self.y - other)

    def __rsub__(self, other):
        other = self.__maths_check(other, "subtracted")
        return Data(self.x, other - self.y)

    def __mod__(self, other):
        """Performs the modulus with the y values."""
        other = self.__maths_check(other, "divided mod")
        return Data(self.x, self.y % other)

    def __rmod__(self, other):
        other = self.__maths_check(other, "divided mod")
        return Data(self.x, other % self.y)

    def __floordiv__(self, other):
        """Floor division on the y values."""
        other = self.__maths_check(other, "floor division")
        return Data(self.x, self.y // other)

    def __rfloordiv__(self, other):
        other = self.__maths_check(other, "floor division")
        return Data(self.x, other // self.y)

    def __pow__(self, other):
        """Takes the power of the y values."""
        other  = self.__maths_check(other, "exponentiated")
        return Data(self.x, self.y ** other)

    def __rpow__(self, other):
        other = self.__maths_check(other, "exponentiated")
        return Data(self.x, other ** self.y)

    def __abs__(self):
        """Calculates the absolute value of the y values.
        """
        return Data(self.x, abs(self.y))

    def __neg__(self):
        """Negates the y values"""
        return Data(self.x, neg(self.y))

    def __pos__(self):
        """Performs a unity operation on y values"""
        return Data(self.x, pos(self.y))

    def __eq__(self, other):
        """Data class is only equal to other Data classes with the same data.
        """
        if type(other) != type(self):
            return False
        else:
            return np.array_equal(self.values, other.values)

    def __iter__(self):
        """The iteration happens on the values, like if was numpy array.
        """
        return iter(self.values)

    def __index_check(self, k):
        """Check an index given if it is correct type and size.
        
        Raises errors if it is the wrong type or shape. Also returns a bool
        which is true if only one item is called.

        Parameters
        ----------
        k : slice or can be passed to :func:slice
            A object obtained from index calls

        Returns
        -------
        individual : bool
            Is the index call only for one item?
        """
        if isinstance(k, tuple):
            raise IndexError(
                "Data object only accepts one index")
        elif isinstance(k, slice):
            return False
        try:
            k = np.asarray(k)
        except:
            raise IndexError(
                "Data cannot index with this type.")
        if k.size == 1:
            return True
        elif k.ndim != 1:
            raise IndexError(
                "Data objec can only Index is one dimension.")
        elif k.size != self.x.size:
            raise IndexError(
                f"Index given was wrong length. The length of index was "
                f"{k.size} and the Data is length {self.x.size}")
        else:
            return False


    def __getitem__(self, k):
        """Indexing returns a subset of the Data object.

        If given a slice or and array of boolean a new Data object is 
        produced. If given a int a length two array with [x, y] is returned. 
        """
        if self.__index_check(k):
            return self.values(k)
        else:
            return Data(self.values[k])

    def __setitem__(self, k, v):
        """Item assignment is not allowed in Data objects.

        This kind of action is possible with the functions :meth:`set_x`, 
        :meth:`set_y`, and :meth:`set_data`.
        """
        raise TypeError(
            "Data objects do not allow item assignment. For this "
            "functionality see .set_x, .set_y, and .set_data.")

    def set_x(self, k, v):
        """This is used for setting x values.

        Parameters
        ----------
        k : slice
            Objects that can be passed to a :class:`numpy.ndarray` as 
            an index.
        v : numpy.ndarray
            The values to assign to the indexed values. 
        """
        if isinstance(v, Data):
            raise TypeError(
                "Cannot set the object type with a Data object.")
        self.__index_check(k)
        new_x = self.x
        new_x[k] = v
        self.__init__(new_x, self.y)

    def set_y(self, k, v):
        """This is used for setting x values.

        Parameters
        ----------
        k : slice
            Objects that can be passed to a :class:`numpy.ndarray` as 
            an index.
        v : numpy.ndarray
            The values to assign to the indexed values. 
        """
        if isinstance(v, Data):
            raise TypeError(
                "Cannot set the object type with a Data object.")
        self.__index_check(k)
        new_y = self.y
        new_y[k] = v
        self.__init__(self.x, new_y)

    def set_data(self, k, v):
        """This is used for setting x and y values.

        Parameters
        ----------
        k : slice
            Objects that can be passed to a :class:`numpy.ndarray` as 
            an index.
        v : numpy.ndarray, Data
            The values to assign to the indexed values. This can only be a
            two column :class:`numpy.ndarray` or a :class:`Data` object.
        """
        if self.__index_check(k):
            size = 2
        else:
            size = self.values[k].size
        if not isinstance(v, (Data, np.ndarray)):
            raise TypeError(
                f"The value to assign data must be a data object or a two "
                f"column numpy array. The type give was {type(v)}.")
        elif isinstance(v, Data):
            if size != v.values.size:
                raise ValueError(
                    f"The Data to set is a different size to the Data "
                    f"object given. The size to index was {size/2} "
                    f"while the data to set was {v.values.size/2}.")
            else:
                new_data = self.values
                new_data[k] = v.values
        elif v.ndim != 2:
            raise ValueError(
                f"The dimension of the numpy array to set two is not "
                f"the correct shape. Needs to be a two column array shape "
                f"given was {v.shape}.")
        elif v.shape[1] != 2:
            raise ValueError(
                f"The dimension of the numpy array to set two does not "
                f"have two columns. Needs to be a two column array shape "
                f"given was {v.shape}.")
        elif v.size != size:
            raise ValueError(
                f"The Data to set is a different size to the numpy "
                f"array given. The size to index was {size/2} "
                f"while the data to set was {v.size/2}.")
        else:
            new_data = self.values
            new_data[k] = v
        self.__init__(new_data)

    def min_x(self):
        """This provides the lowest value of x

        Returns
        -------
        x_min : float
            The minimum value of x
        """
        return np.min(self.x)

    def max_x(self):
        """This provides the highest value of x

        Returns
        -------
        x_max : float
            The maximum value of x
        """
        return np.max(self.x)

    def spacing_x(self):
        """Returns the average spacing in x

        Returns
        -------
        x_max : float
            The average spacing in the x data
        """
        return (self.max_x() - self.min_x())/len(self)    

    def y_from_x(self, x_val, bounds_error=True):
        """Gives the y value for a certain x value or set of x values.

        Parameters
        ----------
        x_val : float
            X values to interpolate y values from.
        bounds_error : bool, optional
            If an error should thrown in x value is out of range, 
            default True.
        
        Returns
        -------
        y_val : float or numpy.ndarray
            Corresponding to the requested x values in an array if only one 
            value is given a float is returned.
        """
        if bounds_error and \
            (np.max(x_val)>self.max_x() or np.min(x_val)<self.min_x()):
            raise ValueError(
                f"The given x_values are out side of the range of data "
                f"which is between {self.min_x()} and {self.max_x()}")

        y_val = interp1d(self.x, self.y, bounds_error=False,
            fill_value=(self.y.min(), self.y.max()))(x_val)
        if y_val.size != 1:
            return y_val
        else:
            return float(y_val)

    def x_cut(self, x_min, x_max):
        """This cuts the data to a region between x_min and x_max.
        
        Parameters
        ----------    
        x_min : float
            The minimal x value to cut the data.
        x_max : float
            The maximal x value to cut the data.
        
        Returns
        -------
        cut_data : Data    
            A data object with the values cut to the given x range.
        """
        if x_min > x_max:
            raise ValueError('x_min should be smaller than x_max')
        return Data(self.values[
                    np.searchsorted(self.x, x_min, side='left'):
                    np.searchsorted(self.x, x_max, side='right'), :])

    def strip_nan(self):
        """This removes any row which has a nan or infinite values in.
        
        Returns
        -------
        striped_data : Data
            Data class without non-finite values in.
        """
        return Data(self.values[np.isfinite(self.values).any(axis=1)])

    def sort(self):
        """Sorts the data set in x and returns the new array.

        Returns
        -------
        sorted_data : Data
            A Data class with the sorted data.
        """
        return Data(self.values[np.argsort(self.x), :])

    def interp_range(self, min_x, max_x, step_size, **kwargs):
        """Evenly interpolates in x the data between a min and max value.

        This is used for combining datasets with corresponding but different 
        x values. It uses :func:`scipy.interpolate.interp1d` and 
        ``**kwargs`` can be pass to it.
        
        Parameters
        ----------
        data_set :Data
            The data set to be interpolated.
        min_x :float
            The minimum x value in the interpolation.
        max_y : float
            The maximum x value in the interpolation.
        step_size : float
            The step size between each point.
        
        Returns
        -------
        interpolated_data : Data
            A new data set with evenly interpolated points.
        """
        if np.min(self.x) > min_x:
            raise ValueError("min_x value to interpolate is below data")
        if np.max(self.x) < max_x:
            raise ValueError("max_x value to interpolate is above data")
        x_vals = np.arange(min_x, max_x, step_size)
        y_vals = interp1d(self.x, self.y, bounds_error=False,
            fill_value=(self.y.min(), self.y.max()))(x_vals)
        return Data(x_vals, y_vals)

    def to_range(self, min_x, max_x, step_size, **kwargs):
        '''
This evenly interpolates the data points between a min
and max x value. This is used so that the different
data objects can be combined with the same x-axis. This changes
the object.
It uses scipy.interpolate.interp1d and **kwargs can be pass to it.
Args:
    data_set (Data): The data set to be interpolated
    min_x (float): The minimum x value in the interpolation
    max_y (float): The maximum x value in the interpolation
    step_size (float): The step size between each point
'''
        if np.min(self.x) > min_x:
            raise ValueError("min_x value to interpolate is below data")
        if np.max(self.x) < max_x:
            raise ValueError("max_x value to interpolate is above data")
        x_vals = np.arange(min_x, max_x, step_size)
        y_vals = interp1d(self.x, self.y, bounds_error=False,
            fill_value=(self.y.min(), self.y.max()))(x_vals)
        # sets the attributes
        self.__init__(x_vals, y_vals)
        return self


    def interp_full(self, step_size, **kwargs):
        """
This interpolates the data to give an even spacing. This is useful
for combining different data sets.
It uses scipy.interpolate.interp1d and **kwargs can be pass to it.
Args:
    step_size (float): The spacing of the data along x.
Return:
    A Data class with the interpolated data.
"""
        x_start = np.ceil(self.x.min()/step_size)*step_size
        x_stop = np.floor(self.x.max()/step_size)*step_size
        x_vals = np.linspace(x_start, x_stop,
                           int(round((x_stop - x_start)/step_size)) + 1)
        y_vals = interp1d(self.x, self.y, **kwargs)(x_vals)
        return Data(x_vals, y_vals)

    def interp_number(self, point_number, **kwargs):
        """
This interpolates the data to give an even spacing. This is useful
for saving data of different types together
It uses scipy.interpolate.interp1d and **kwargs can be pass to it.
Args:
    point_number (int): The spacing of the data along x.
Return:
    A Data class with the interpolated data.
"""

        x_vals = np.linspace(self.x.min(), self.x.max(),
                             int(point_number))
        y_vals = interp1d(self.x, self.y, **kwargs)(x_vals)
        return Data(x_vals, y_vals)

    def to_even(self, step_size, **kwargs):
        """
This interpolates the data to give an even spacing, and changes
the data file.
It uses scipy.interpolate.interp1d and **kwargs can be pass to it.
Args:
    step_size (float): The spacing of the data along x.
"""
        x_start = np.ceil(self.x.min()/step_size)*step_size
        x_stop = np.floor(self.x.max()/step_size)*step_size
        x_vals = np.linspace(x_start, x_stop,
                           int(round((x_stop - x_start)/step_size)) + 1)
        y_vals = interp1d(self.x, self.y, **kwargs)(x_vals)
        # Set the attributes
        self.__init__(x_vals, y_vals)
        return self

    def apply_x(self, function):
        """
This takes a function and applies it to the x values.
Args:
    function (func): THe function to apply to the x values
Returns:
    Data class with new x values
"""
        return Data(function(self.x), self.y)

    def apply_y(self, function):
        """
This takes a function and applies it to the y values.
Args:
    function (func): THe function to apply to the y values
Returns:
    Data class with new x values
"""
        return Data(self.x, function(self.y))

    def plot(self, *args, axis=None, **kwargs):
        """
Simple plotting function that runs
matplotlib.pyplot.plot(self.x, self.y, *args, **kwargs)
Added a axis keyword which operates so that if given
axis.plot(self.x, self.y, *args, **kwargs)
"""
        if axis == None:
            plt.plot(self.x, self.y, *args, **kwargs)
        else:
            axis.plot(self.x, self.y, *args, **kwargs)

    def to_csv(self, filename, columns=["X", "Y"], **kwargs):
        """
        Saves the resistance vs field as a csv
        uses pandas.DataFrame.to_csv and kwargs are pass to it
        Args:
            filename (str): filename to save the data as
            columns : [str, str]
                The title of the two columns
        """
        pd.DataFrame(self.values, columns=columns
            ).to_csv(filename, **kwargs)


def sum_data(data_list):
    """
Preforms the sum of the y data a set of Data class objects.
Args:
    data_list (list of Data): List of Data objects to sum together.
Returns:
    A Data object which is the sum of the y values of the original
        data sets.
"""
    total = data_list[0]
    for data_set in data_list[1:]:
        total += data_set.y
    return total


def mean(data_list):
    """
Preforms the mean of the y data a set of Data class objects.
Args:
    data_list (list of Data): List of Data objects to combine together.
Returns:
    A Data object which is the average of the y values of the original
        data sets.
"""
    return sum_data(data_list)/len(data_list)


def save_arrays(array_list, column_names, file_name, **kwargs):
    """This saves a collection of one dimensional :class:`numpy.ndarray` 
    stored in a list into a .csv file. It does this by passing it to a 
    :class:`pandas.DataFrame` object and using the method `to_csv`. If the 
    arrays are different lengths the values are padded with NaNs.
    kwargs are passed to :meth:`pandas.DataFrame.to_csv`

    Parameters
    ----------
    array_list : [numpy.ndarray]
        A list of 1d numpy.ndarrays to save to the .csv file
    columns_names : [str]
        A list of column names for the .csv file the same length as the list 
        of data arrays
    file_name : str
        The file name to save the file as
    """
    if not isinstance(array_list, list):
        raise TypeError("array_list is not a list.")
    elif not isinstance(column_names, list):
        raise TypeError("column_names is not a list.")
    elif len(array_list) != len(column_names):
        raise ValueError("array_list and column_names are not "
            "the same lenght.")
    max_length = 0
    for arr in array_list:
        if not isinstance(arr, np.ndarray):
            raise ValueError("array_list contains objects that are not "
                "numpy arrays.")
        elif len(arr.shape) != 1:
            raise ValueError("array_list arrays are not 1D.")
        elif max_length < arr.size:
            max_length = arr.size
    to_concat = []
    for arr in array_list:
        to_concat.append(np.pad(arr, (0, max_length - arr.size),
            mode='constant',
            constant_values=np.nan)[:, None])
    to_save = np.concatenate(to_concat, axis=1)
    if 'index' not in kwargs.keys():
        kwargs['index'] = False
    pd.DataFrame(to_save, columns=column_names).to_csv(file_name, **kwargs)


def save_data(data_list, data_names, file_name, 
    x_name='X', y_name='Y', name_space='_', **kwargs):
    """Saves a list of data objects in to a .csv file.

    This works by passing to :func:`save_arrays` and subsequently to 
    :meth:`pandas.DataFrame.to_csv`. kwargs are passed to 
    :meth:`pandas.DataFrame.to_csv`

    Parameters
    ----------
    data_list : [gigaanalysis.data.Data]
        A list of Data objects to be saved to a .csv file
    data_names : [str]
        A list the same length as the data list of names of each of the data 
        objects. These will make the first half of the column name in the 
        .csv file.
    file_name : str
        The name the file will be saved as
    x_name : str, optional
        The string to be append to the data name to indicate the x column in 
        the file. Default is 'X'
    y_name : str, optional
        The string to be append to the data name to indicate the y column in 
        the file. Default is 'Y'
    name_space : str, optional
        The string that separates the data_name and the x or y column name 
        in the column headers in the .csv file. The default is '_'.
    """
    if not isinstance(data_list, list):
        raise TypeError("data_list is not a list.")
    elif not isinstance(data_names, list):
        raise TypeError("data_names is not a list.")
    elif len(data_list) != len(data_names):
        raise ValueError("data_list and data_names are not "
            "the same lenght.")
    array_list = []
    for dat in data_list:
        if not isinstance(dat, Data):
            raise ValueError("data_list contains objects that are not "
                "Data objects.")
        array_list.append(dat.x)
        array_list.append(dat.y)
    column_names = []
    for name in data_names:
        column_names.append(name + name_space + x_name)
        column_names.append(name + name_space + y_name)
    save_arrays(array_list, column_names, file_name, **kwargs)


def save_dict(data_dict, file_name,
    x_name='X', y_name='Y', name_space='/', **kwargs):
    """Saves a dictionary of data objects in to a .csv file.

    This works by passing to :func:`save_data` and subsequently to 
    :meth:`pandas.DataFrame.to_csv`. The names of the data objects are taken 
    from  the keys of the data_dict. kwargs are passed to 
    :meth:`pandas.DataFrame.to_csv`

    Parameters
    ----------
    data_list : [gigaanalysis.data.Data]
        A dictionary of Data objects to be saved to a .csv file. The keys of 
        the dictionary will be used as the data names when passed to 
        :func:`save_data`.
    file_name : str
        The name the file will be saved as
    x_name : str, optional
        The string to be append to the data name to indicate the x column in 
        the file. Default is 'X'
    y_name : str, optional
        The string to be append to the data name to indicate the y column in 
        the file. Default is 'Y'
    name_space : str, optional
        The string that separates the data_name and the x or y column name 
        in the column headers in the .csv file. The default is '/'.
    """
    if not isinstance(data_dict, dict):
        raise TypeError("data_dict is not a dictionary.")
    for dat in data_dict.values():
        if not isinstance(dat, Data):
            raise ValueError("data_dict contains values which are not "
                "Data objects.")
    save_data(list(data_dict.values()), list(data_dict.keys()), file_name,
        x_name=x_name, y_name=y_name, name_space=name_space, **kwargs)


def gen_rand(n, func=None, seed=None):
    """Produces Data object with random values.

    This uses :meth:`numpy.random.Generator.random` to produce a
    :class:`Data` object. The numbers in both x and y values are continually 
    increasing in steps between 0 and 1. A function can be applied to the y 
    values.

    Parameters
    ----------
    n : int
        Number of data point to have in the object
    func : function
        A function with one parameter to transform the y values
    seed : float
        Seed to be passed to :func:`numpy.random.default_rng`

    Returns
    -------
    data : :class:`Data`
        The generated data object. 
    """
    if not isinstance(n, (int, np.int_)):
        raise TypeError("n needs to be an int")
    elif n < 1:
        raise ValueError("n need to be a positive integer")
    if not func:
        return Data(
            np.cumsum(np.random.default_rng(seed).random((n, 2)),
                axis=0))
    else:
        return Data(
            np.cumsum(np.random.default_rng(seed).random((n, 2)),
                axis=0)).apply_y(func)

