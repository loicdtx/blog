---
layout: post
title: Geopackage
date: 2017-07-08
summary: RIP shapefile
logo: map-marker
---

TLDR: There are really no reasons to keep using shapefiles, use geopackage (`.gpkg`) instead.

[Geopackage](http://www.geopackage.org/) is an open file format to store geographical data in vector format (and apparently also raster format, but we'll focus on the vector part for now). The format has been around for a few years, but it only caught my attention recently when it was mentioned on the R-SIG-geo mailing list [post](http://r-sig-geo.2731867.n2.nabble.com/proj4string-read-by-readOGR-doesn-t-seem-to-precisely-specify-source-shapefile-projection-td7591243.html#a7591248). I'm usually quite attentive to new things but I definitely missed that one!! Anyway, the reason this caught my attention is that I have been looking for alternatives to shapefile for a long time. So I decided to investigate this gpkg format a bit; particularly how to read and write it with the R and python's main open source libraries, as well as QGIS.

Shapefiles have been around for much longer than I can remember and served us well, but it's no big news that the format has some serious limitations. Let's start with the fact that one file is in fact composed of at least 3 files (usually more); a very inconvenient characteristic when you want to move things around or e-mail data to someone. Shapefiles are like sliced bread, but without any wrapping around it to keep the slices together.
Another, perhaps worse, characteristic of shapefiles is that field names (the names of the columns of the 'attribute table') are limited to 10 characters... yes, just 10!!! I can't recall how many times I've seen the warning message from `writeOGR` telling me that field names were being abbreviated when writing a carefully crafted `Spatial*DataFrame` (`*` being any of `Lines`, `Polygons`, or `Points`) to shapefile; so frustrating!! I wouldn't call shapefiles a nightmare but we're close...
But despite these limitations, shapefiles are ubiquitous, we've all used it, and we almost all agree that it's the 'lingua franca' of the GIS world (as described by Tom MacWright in a rather old but still very informative [blog post](https://macwright.org/2012/10/31/gis-with-python-shapely-fiona.html)).

My previous attempts to find alternatives to shapefiles were not entirely successful. I tried [spatialite](https://en.wikipedia.org/wiki/SpatiaLite) a few years ago, but faced some limitations when trying to write multiple layers to a single file. Another limitation of spatialite is its weight; an empty spatialite database will take about 6MB of disk space; not exactly my definition of lightweight. So at the end I was left telling people that shapefiles are 'bad' but without being able to propose any reasonable alternative. The word *reasonable* is important here as not everyone wants to setup a postGIS database to visualize a bunch of GPS points. An ideal format would be lightweight, self contained, and easy to use for non GIS specialist. GPKG appears to fulfill that role perfectly, finally!!

So let's see how this geopackage format plays with the tools I usually use to read, write and manipulate vector data. First python and then R.

## Python

Fiona is probably the most pythonic library for reading and writing geospatial vector data, and that's what I will use in the example below. When using fiona, you have to work with dictionary representations of your features and these can be written to geospatial files almost as easily as it would be to write a string to a text file. [OGR](http://gdal.org/1.11/ogr/) is obviously the workhorse that enables reading from and writing to the different vector formats. Note that fiona is not the only way to read and write geospatial vector data; geopandas is a very interesting project as well which can do as much with a slightly different data structure and philosophy. But we'll stick to fiona here.

> Note: fiona may come in the form of a binary wheel when installed with pip. This means that it comes with its own version of gdal/OGR, to which it is statically linked. Unfortunately the binaries that come with the current fiona version (1.7.7) do not include the geopackage driver. It might therefore be necessary to install fiona from source in order to allow it to dynamically link to your system gdal. Don't freak out, this is actually pretty easy, just run `pip install -I fiona --no-binary fiona` and you will be good to go.

The code below queries the coordinates of some cities where I've lived (I admit selecting only those with a non ambiguous name, ... no spaces, accents or dashes), builds the features and writes them to a geopackage file.

```python
import fiona
from fiona.crs import from_string
import requests

# Some city where I've lived
cities = ['rompon', 'angers', 'wageningen']

# To write data with fiona, we first have to define a schema, and the crs, that
# we'll pass as arguments when opening the connection to the file.
# After that, features are added one by one by writting a dictionary representation
# of that feature.
schema = {'geometry': 'Point',
          'properties': [('name', 'str'),
                         ('country', 'str')]}

crs = from_string('+proj=longlat +ellps=WGS84 +datum=WGS84 +no_defs')

# Feature builder
def feature_from_name(city):
    r = requests.get("https://maps.googleapis.com/maps/api/geocode/json",
                     params={'address': city})
    coord = r.json()['results'][0]['geometry']['location']
    geometry = {'type': 'Point', 'coordinates': [coord['lng'], coord['lat']]}
    country = r.json()['results'][0]['address_components'][3]['long_name']
    feature = {'geometry': geometry,
               'properties': {'name': city,
                              'country': country}}
    return feature


# Open connection with gpkg file in a context manager and write features to it
with fiona.open('/home/loic/sandbox/cities_fiona.gpkg', 'w',
                layer='points',
                driver='GPKG',
                schema=schema,
                crs=crs) as dst:
    for city in cities:
        feature = feature_from_name(city)
        dst.write(feature)
```

Writing a feature collection to geopackage with fiona is therefore very similar to writing to a shapefile; the only difference is that you have to specify the layer name (only if you want to use the multi-layer capabilities of geopackage). We can verify that the features were properly written by running `ogrinfo`.

```sh
ogrinfo cities_fiona.gpkg

# INFO: Open of `cities_fiona.gpkg'
#       using driver `GPKG' successful.
# 1: points (Point)

# And to get the layer specific information
ogrinfo cities_fiona.gpkg points

# Layer name: points
# Geometry: Point
# Feature Count: 3
# Extent: (-0.563166, 44.781400) - (5.665390, 51.969200)
# Layer SRS WKT:
# GEOGCS["WGS 84",
#     DATUM["WGS_1984",
#         SPHEROID["WGS 84",6378137,298.257223563,
#             AUTHORITY["EPSG","7030"]],
#         AUTHORITY["EPSG","6326"]],
#     PRIMEM["Greenwich",0,
#         AUTHORITY["EPSG","8901"]],
#     UNIT["degree",0.0174532925199433,
#         AUTHORITY["EPSG","9122"]],
#     AUTHORITY["EPSG","4326"]]
# FID Column = fid
# Geometry Column = geom
# name: String (0.0)
# country: String (0.0)
# OGRFeature(points):1
#   name (String) = rompon
#   country (String) = France
#   POINT (4.7174062 44.7813992)

# OGRFeature(points):2
#   name (String) = angers
#   country (String) = France
#   POINT (-0.563166 47.478419)

# OGRFeature(points):3
#   name (String) = wageningen
#   country (String) = Netherlands
#   POINT (5.6653948 51.9691868)
```

Everything looks good and that's already great but geopackage is supposed to be able to handle multiple layer. So let's try to build another layer with a different geometry type and write it to the same file.
The code below builds buffers around each feature and writes the newly created polygon feature collection to another layer of the geopackage file.

```python
import fiona
import pyproj
from shapely.geometry import Point, mapping

file_name = '/home/loic/sandbox/cities_fiona.gpkg'

# Define a function that can build a buffer feature from a point feature
# The different steps for that are:
# - Define a local equidistant coordinate reference system
# - Build a Point geometry in that coordinate reference system
# - Make a buffer around the point
# - Create a dictionary representation of the polygon geometry
# - Reproject the polygon back to the original coordinate reference system
def buffer_from_point_feature(feature, distance):
    prj = pyproj.Proj(proj='aeqd', lat_0=feature['geometry']['coordinates'][0],
                      lon_0=feature['geometry']['coordinates'][1])
    geom = Point(prj(*feature['geometry']['coordinates']))
    buffer = geom.buffer(distance)
    feature_out = {'geometry': mapping(buffer),
                   'properties': feature['properties']}
    x_ll, y_ll = prj(*zip(*feature_out['geometry']['coordinates'][0]), inverse=True)
    coord_ll = [zip(x_ll, y_ll)]
    feature_out['geometry']['coordinates'] = coord_ll
    return feature_out


# Read the data back
with fiona.open(file_name, layer = 'points') as src:
    # Load all features in memory because it seems that opening two simultaneous connections
    # to the same file does not work	
    buffer_collection = [buffer_from_point_feature(x, 100000) for x in src]
    schema = src.schema
    crs = src.crs


schema.update(geometry='Polygon')

with fiona.open(file_name, 'w', layer='polygons', driver='GPKG',
                schema=schema, crs=crs) as dst:
    for feature in buffer_collection:
        dst.write(feature)
```

A second layer named `polygons` has now been added to the file, we could check once again with `ogrinfo` but let's see whether the layers can be opened in QGIS instead.
When selecting the geopackage file, QGIS offers to choose which of the layers contained in the file to open; either or both can be selected, and they will be opened and displayed normally, just like any other vector layer would.

![](/blog/images/geopackage_qgis_preview.png)

## R

Now that we know that python can read and write geopackage files and even handles multiple layers, let's see what are R capabilities to perform the same tasks.

A small reminder about R and spatial data; there are two packages to work with vector data; `sp` and `sf`.
The two packages are absolutely not competitors, they are actually from the same people (in particular Edzer Pebesma and Roger Bivand who have been very consistent members/contributors of the R spatial community basically since its beginning).
So `sf` is sort of the new iteration of `sp`. The idea of the `sf` package is described in [this blog post](http://r-spatial.org/r/2016/02/15/simple-features-for-r.html), and in the original [project proposal](https://github.com/edzer/sfr/blob/master/PROPOSAL.md).
With `sp` data can be read and written using `readOGR` and `writeOGR` respectively, while `st_read` and `st_write` play that role in `sf`. 

The code below more or less reproduces the steps of the python example above.
First, coordinates of a vector of cities are queried to the google maps API, the result is coerced to a `sf` dataframe, buffer are computer around the cities and both layers are written to a single geopackage file.
Note that I took a shortcut in the buffering step and did not project the data prior to buffering as I should have done.

```R
library(sf)
library(httr)

cities <- c('rompon', 'angers', 'wageningen')

# Function to query city location and build a dataframe row
cityInfo <- function(x){
  r <- GET('https://maps.googleapis.com/maps/api/geocode/json', query = list(address = x))
  data.frame(lat=content(r)$results[[1]]$geometry$location$lat,
             lon=content(r)$results[[1]]$geometry$location$lng,
             name=x,
             country=content(r)$results[[1]]$address_components[[4]]$long_name)
}

df <- do.call(rbind, lapply(cities, cityInfo))
sf_df <- st_as_sf(df, coords = c("lon", "lat"), crs = '+proj=longlat +ellps=WGS84 +datum=WGS84 +no_defs')
st_write(sf_df, dsn = '/home/loic/sandbox/cities_sf.gpkg', layer = 'cities_point')

# Generate buffers (in degrees)
sf_df_buffer <- st_buffer(sf_df, 0.1)
st_write(sf_df_buffer, dsn = '/home/loic/sandbox/cities_sf.gpkg', layer = 'cities_polygon')
```

Thanks to the leaflet package it's easy to visualize the spatial objects created in an interactive webmap.

<iframe src="/blog/html/geopackage_leaflet.html" name="targetframe" scrolling="no" frameborder="0" style="display: block; padding: 10px 10px; width: 100%; height: 300px; border: 0px;">
    </iframe>

We can try with `sp` as well, starting from the `df` object created above.

```R
library(sp)
library(rgeos)
library(rgdal)

spdf <- SpatialPointsDataFrame(coords = df[,c('lon', 'lat')], data=df[,c('name', 'country')],
			       proj4string=CRS('+proj=longlat +ellps=WGS84 +datum=WGS84 +no_defs'))

spdf_buffer <- gBuffer(spdf, byid=TRUE, width=1)

writeOGR(spdf, dsn='/home/loic/sandbox/cities_sp.gpkg', layer='cities_point', driver='GPKG')
writeOGR(spdf_buffer, dsn='/home/loic/sandbox/cities_sp.gpkg', layer='cities_polygon', driver='GPKG')
```

Although the code completes successfully, if you check the geopackage file created you'll notice that only the last written layer is retained.
`writeOGR` appears not to be able to update the file and add new layers, but creates a new file on every call instead.
When writing `sp` objects with `writeOGR` you'll therefore need to create a separate file for each layer.
This is not optimal but still better than the shapefile option. 

# Conclusion

So to conclude:

- Geopackage is a convenient, lightweight, geospatial data storage format
- It's mature and fully operable with the common GIS tools (QGIS, ArcGIS, R, python) 
- I found only one minor limitation; the lack of multi-layer support of `writeOGR`
- Writing this post took longer than expected


If you're a GIS guy, give it a try and promote geopackage around you, to your colleagues and collaborators; if you teach GIS, introduce it as the preferred data storage option; and if you're neither of these then I really wonder why you are reading that right now... ;-) 

I can not longer find a good reason to keep using shapefiles. Can you?

