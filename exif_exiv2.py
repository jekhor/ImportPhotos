import os
import uuid
import pyexiv2

def _get_if_exist(data, key):
    if key in data:
        return data[key]

    return None

def _convert_to_degrees(tag):
    d, m, s = tag.value

    return d + (m / 60.0) + (s / 3600.0)

def get_exif_location(exif_data):
    """
    Returns the latitude and longitude, if available, from the provided exif_data (obtained through get_exif_data above)
    """

    lat = ''
    lon = ''
    gps_latitude = _get_if_exist(exif_data, 'Exif.GPSInfo.GPSLatitude')
    gps_latitude_ref = _get_if_exist(exif_data, 'Exif.GPSInfo.GPSLatitudeRef')
    gps_longitude = _get_if_exist(exif_data, 'Exif.GPSInfo.GPSLongitude')
    gps_longitude_ref = _get_if_exist(exif_data, 'Exif.GPSInfo.GPSLongitudeRef')

    if gps_latitude and gps_latitude_ref and gps_longitude and gps_longitude_ref:
        lat = _convert_to_degrees(gps_latitude)
        if gps_latitude_ref.value != 'N':
            lat = 0 - lat

        lon = _convert_to_degrees(gps_longitude)
        if gps_longitude_ref.value != 'E':
            lon = 0 - lon

    return lat, lon

def get_geo_info(imgpath, RelPath, ImagesSrc):
    name = os.path.basename(imgpath)
    uuid_ = str(uuid.uuid4())

    altitude = ''
    date = ''
    time_ = ''
    timestamp = ''
    north = ''
    azimuth = ''
    maker = ''
    model = ''
    title = ''
    user_comm = ''
    focal_length_35mm = None
    xmp_tags = {}

    md = pyexiv2.ImageMetadata(imgpath)
    md.read()

    if not 'Exif.GPSInfo.GPSLatitude' in md.exif_keys:
        return None, None, None

    if not 'Exif.GPSInfo.GPSLongitude' in md.exif_keys:
        return None, None, None

    lat, lon = get_exif_location(md)

    try:
            altitude = float(md['Exif.GPSInfo.GPSAltitude'].value)
    except:
        pass

    try:
        dt1 = md['Exif.Photo.DateTimeOriginal'].value
        date = str(dt1.date())
        time_ = str(dt1.time())
        timestamp = dt1.isoformat()
    except:
        pass

    try:
        azimuth = float(md['Exif.GPSInfo.GpsImgDirection'].value)
    except:
        pass

    try:
        north = md['Exif.GPSInfo.GpsImgDirectionRef'].value
    except:
        pass

    try:
        maker = md['Exif.Image.Make'].value
    except:
        pass

    try:
        model = md['Exif.Image.Model'].value
    except:
        pass

    try:
        title = md['Exif.Image.ImageDescription'].value
    except:
        pass

    try:
        user_comm = md['Exif.Photo.UserComment'].value
    except:
        pass

    try:
        focal_length_35mm = md['Exif.Photo.FocalLengthIn35mmFilm'].value
    except:
        pass

    for k in md.xmp_keys:
        try:
            xmp_tags[k] = float(md[k].value)
        except:
            xmp_tags[k] = str(md[k].value)

    # Calculate camera azimuth based on info about drone and gimbal yaw angles
    if not azimuth and 'Xmp.drone-dji.FlightYawDegree' in md.xmp_keys:
        azimuth = float(md['Xmp.drone-dji.FlightYawDegree'].value) + 180.0

        if 'Xmp.drone-dji.GimbalYawDegree' in md.xmp_keys:
            azimuth += float(md['Xmp.drone-dji.GimbalYawDegree'].value) + 180.0

        if azimuth > 360:
            azimuth -= 360

        north = 'T'


    geo_info = {
            "type": "Feature",
            "properties": {'ID': uuid_, 'Name': name, 'Date': date, 'Time': time_,
                'Lon': lon,
                'Lat': lat, 'Altitude': altitude, 'North': north,
                'Azimuth': azimuth,
                'Camera Maker': maker, 'Camera Model': model, 'Title': title,
                'FocalLength35mm': focal_length_35mm,
                'Comment': user_comm,'Path': imgpath, 'RelPath': RelPath,
                'Timestamp': timestamp, 'Images': ImagesSrc
                },
            "geometry": {"coordinates": [lon, lat], "type": "Point"}
            }

    if xmp_tags:
        geo_info["properties"].update(xmp_tags)

    return lon, lat, geo_info

