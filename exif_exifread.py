import os
import uuid
import exifread

def _get_if_exist(data, key):
    if key in data:
        return data[key]

    return None


def _convert_to_degress(value):
    """
    Helper function to convert the GPS coordinates stored in the EXIF to degress in float format

    :param value:
    :type value: exifread.utils.Ratio
    :rtype: float
    """
    d = float(value.values[0].num) / float(value.values[0].den)
    m = float(value.values[1].num) / float(value.values[1].den)
    s = float(value.values[2].num) / float(value.values[2].den)

    return d + (m / 60.0) + (s / 3600.0)

def get_exif_location(exif_data, lonlat):
    """
    Returns the latitude and longitude, if available, from the provided exif_data (obtained through get_exif_data above)
    """

    if lonlat=='lonlat':
        lat = ''
        lon = ''
        gps_latitude = _get_if_exist(exif_data, 'GPS GPSLatitude')
        gps_latitude_ref = _get_if_exist(exif_data, 'GPS GPSLatitudeRef')
        gps_longitude = _get_if_exist(exif_data, 'GPS GPSLongitude')
        gps_longitude_ref = _get_if_exist(exif_data, 'GPS GPSLongitudeRef')

        if gps_latitude and gps_latitude_ref and gps_longitude and gps_longitude_ref:
            lat = _convert_to_degress(gps_latitude)
            if gps_latitude_ref.values[0] != 'N':
                lat = 0 - lat

            lon = _convert_to_degress(gps_longitude)
            if gps_longitude_ref.values[0] != 'E':
                lon = 0 - lon

        return lat, lon

def get_geo_info(imgpath, RelPath, ImagesSrc):
    name = os.path.basename(imgpath)

    with open(imgpath, 'rb') as imgpathF:
        tags = exifread.process_file(imgpathF, details=False)

    if not tags.keys() & {"GPS GPSLongitude", "GPS GPSLatitude"}:
        return (None, None, None)

    lat, lon = get_exif_location(tags, "lonlat")
    try:
        if 'GPS GPSAltitude' in tags:
            altitude = float(tags["GPS GPSAltitude"].values[0].num) / float(
                tags["GPS GPSAltitude"].values[0].den)
        else:
            altitude = ''
    except:
        altitude = ''
    uuid_ = str(uuid.uuid4())

    try:
        dt1, dt2 = tags["EXIF DateTimeOriginal"].values.split(' ')
        date = dt1.replace(':', '/')
        time_ = dt2
        timestamp = dt1.replace(':', '-') + 'T' + time_
    except:
        try:
            date = tags["GPS GPSDate"].values.replace(':', '/')
            tt = [str(i) for i in tags["GPS GPSTimeStamp"].values]
            time_ = "{:0>2}:{:0>2}:{:0>2}".format(tt[0], tt[1], tt[2])
            timestamp = tags["GPS GPSDate"].values.replace(':', '-') + 'T' + time_
        except:
            date = ''
            time_ = ''
            timestamp = ''

    try:
        if 'GPS GPSImgDirection' in tags:
            azimuth = float(tags["GPS GPSImgDirection"].values[0].num) / float(
                tags["GPS GPSImgDirection"].values[0].den)
        else:
            azimuth = ''
    except:
        azimuth = ''

    try:
        if 'GPS GPSImgDirectionRef' in tags:
            north = str(tags["GPS GPSImgDirectionRef"].values)
        else:
            north = ''
    except:
        north = ''

    try:
        if 'Image Make' in tags:
           maker = tags['Image Make']
        else:
            maker = ''
    except:
        maker = ''

    try:
        if 'Image Model' in tags:
            model = tags['Image Model']
        else:
            model = ''
    except:
        model = ''

    try:
        if 'Image ImageDescription' in tags:
            title = tags['Image ImageDescription']
        else:
            title = ''
    except:
        title = ''

    try:
        if 'EXIF UserComment' in tags:
            user_comm = tags['EXIF UserComment'].printable
        else:
            user_comm = ''
    except:
        user_comm = ''

    geo_info = {
            "type": "Feature",
            "properties": {'ID': uuid_, 'Name': name, 'Date': date, 'Time': time_,
                'Lon': lon,
                'Lat': lat, 'Altitude': altitude, 'North': north,
                'Azimuth': azimuth,
                'Camera Maker': str(maker), 'Camera Model': str(model), 'Title': str(title),
                'Comment': user_comm,'Path': imgpath, 'RelPath': RelPath,
                'Timestamp': timestamp, 'Images': ImagesSrc},
            "geometry": {"coordinates": [lon, lat], "type": "Point"}
            }

    return (lon, lat, geo_info)

