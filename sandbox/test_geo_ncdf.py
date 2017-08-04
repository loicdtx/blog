import netCDF4 as nc
import numpy as np
from rasterio.crs import CRS
from affine import Affine

# import os
# from datetime import date
from pprint import pprint

file1 = '/home/ldutrieux/sandbox/test_data/nc/test.nc'

meta = {'width': 3000,
        'height': 2000,
        'crs': CRS({u'lon_0': 0, u'ellps': u'WGS84', u'y_0': 0, u'no_defs': True,
                    u'proj': u'laea', u'x_0': 0, u'units': u'm', u'lat_0': 0}),
        'transform': Affine(1000, 0, 0, 0, -1000, 0),
        'count': 100,
}

array = np.random.rand(meta['height'], meta['width'])

with nc.Dataset(file1, mode='w') as src:
    # Create spatial dimensions
    x_dim = src.createDimension('x', meta['width'])
    y_dim = src.createDimension('y', meta['height'])
    # Create temporal dimension
    t_dim = src.createDimension('time', None)
    t_var = src.createVariable('time', 'f8', ('time',))
    t_var.standard_name = 'time'
    t_var.long_name = 'time'
    t_var.units = 'days since 1970-01-01 00:00:00'
    t_var.calendar = 'gregorian'
    # chlor variable
    chlor = src.createVariable('chlor_a', np.float32, ('time','y','x'),
                               zlib=True)
    chlor.grid_mapping = 'laea' # This corresponds to the name of the variable where crs info is stored
    # laea variable to store projection information
    laea = src.createVariable('laea', 'c')
    laea.long_name = "CRS definition"
    laea.spatial_ref = meta['crs'].wkt
    laea.GeoTransform = " ".join(str(x) for x in meta['transform'].to_gdal())
    # pprint(src)

def nc_append(file, variable, array, array_dt):
    """Append an array to existing netcdf file (variable)

    Args:
        file (str): Name of an existing netcdf file
        variable (str): Name of the netcdf variable containing the array (TODO: check
            whether 'group/variable') works too
        array (numpy.array): The 2D array to write to the file. The shape of the
            array must match the spatial dimensions of the netcdf array
        array_dt (datetime.datetime): Date of the array

    Details:
        The file must contain a time variable at the root, with the attributes
            units (in the form <time units> since <reference time>) and calendar
            The variable array must be organized with time as the first dimension,
            then nrow and ncol
    """
    with nc.Dataset(file, 'a') as src:
        # get time variable metadata (unit, origin, calendar)
        time = src['time']
        time_meta = {'units': time.units,
                     'calendar': time.calendar}
        # Get date length (it should be the same as the first dimension of the array, is it worth checking that?)
        ind = time.shape[0]
        # COnvert array_dt to time variable equivalent and write at the right position (append)
        dt_num = nc.date2num(array_dt, **time_meta)
        time[ind] = dt_num
        # Write array to variable
        src[variable][ind,:,:] = array

import datetime

for i in range(50):
    array = np.random.rand(meta['height'], meta['width'])
    nc_append(file1, 'chlor_a', array, datetime.datetime(1987, 11, 21) + datetime.timedelta(i))

