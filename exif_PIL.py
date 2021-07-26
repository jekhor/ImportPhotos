import os
import uuid
from PIL import Image
from PIL.ExifTags import TAGS

def get_geo_info(imgpath, RelPath, ImagesSrc):
    name = os.path.basename(imgpath)

    a = {}
    info = Image.open(imgpath)
    info = info._getexif()

    if info == None:
        return None, None, None

    for tag, value in info.items():
        if TAGS.get(tag, tag) == 'GPSInfo' or TAGS.get(tag, tag) == 'DateTime' or TAGS.get(tag,
                                                                                           tag) == 'DateTimeOriginal':
            a[TAGS.get(tag, tag)] = value

    if a == {}:
        return None, None, None

    if a['GPSInfo'] != {}:
        if 1 and 2 and 3 and 4 in a['GPSInfo']:
            lat = [float(x) for x in a['GPSInfo'][2]]
            latref = a['GPSInfo'][1]
            lon = [float(x) for x in a['GPSInfo'][4]]
            lonref = a['GPSInfo'][3]

            lat = lat[0] + lat[1] / 60 + lat[2] / 3600
            lon = lon[0] + lon[1] / 60 + lon[2] / 3600

            if latref == 'S':
                lat = -lat
            if lonref == 'W':
                lon = -lon
        else:
            return None, None, None

        uuid_ = str(uuid.uuid4())
        if 'DateTime' or 'DateTimeOriginal' in a:
            if 'DateTime' in a:
                dt1, dt2 = a['DateTime'].split()
            if 'DateTimeOriginal' in a:
                dt1, dt2 = a['DateTimeOriginal'].split()
            date = dt1.replace(':', '/')
            time_ = dt2
            timestamp = dt1.replace(':', '-') + 'T' + time_

        try:
            if 6 in a['GPSInfo']:
                if len(a['GPSInfo'][6]) > 1:
                    mAltitude = float(a['GPSInfo'][6][0])
                    mAltitudeDec = float(a['GPSInfo'][6][1])
                    altitude = mAltitude / mAltitudeDec
            else:
                altitude = ''
        except:
            altitude = ''

        try:
            if 16 and 17 in a['GPSInfo']:
                north = str(a['GPSInfo'][16])
                azimuth = float(a['GPSInfo'][17][0]) / float(a['GPSInfo'][17][1])
            else:
                north = ''
                azimuth = ''
        except:
            north = ''
            azimuth = ''

        maker = ''
        model = ''
        user_comm = ''
        title = ''

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

