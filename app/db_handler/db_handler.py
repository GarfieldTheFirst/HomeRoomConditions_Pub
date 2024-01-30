import json
from datetime import datetime
from sqlalchemy import func
from app import db
from app.models.roomdata import Hour, Year, Day, Month, Roomdata, User, Role
from app.models.roomdata import Device as DB_Device


def get_all_stored_users():
    return db.session.query(User).all()


def get_stored_user(**kwargs):
    for key, value in kwargs.items():
        if key == "id":
            user = db.session.query(User).filter_by(id=value).first()
        elif key == "username":
            user = db.session.query(User).filter_by(
                username=value).first()
        else:
            raise Exception
    return user


def delete_stored_users(stored_users):
    for user in stored_users:
        if not user.is_administrator():
            db.session.delete(user)
    db.session.commit()


def modify_stored_user_permissions(stored_users):
    for user in stored_users:
        if user.is_administrator():
            continue
        elif user.is_user():
            user.role = Role.query.filter_by(name='Tentative').first()
        elif user.is_tentative():
            user.role = Role.query.filter_by(name='User').first()
    db.session.commit()


def get_all_stored_devices():
    return db.session.query(DB_Device).all()


def get_stored_device(**kwargs):
    for key, value in kwargs.items():
        if key == "ip":
            device = db.session.query(DB_Device).filter_by(ip=value).first()
        elif key == "name":
            device = db.session.query(DB_Device).filter_by(name=value).first()
        else:
            raise Exception
    return device


def store_new_device(name, ip, connected):
    new_data = DB_Device(name=name,
                         ip=ip,
                         connected=connected,
                         recording=False)
    db.session.add(new_data)
    db.session.commit()


def get_stored_devices_to_be_monitored():
    recording_device_list = []
    for device in get_all_stored_devices():
        if device.recording:
            recording_device_list.append(device)
    return recording_device_list


def set_stored_devices_connected_setting(stored_devices, value):
    for stored_device in stored_devices:
        if stored_device.connected != value:
            stored_device.last_seen = datetime.utcnow()  # update any changes
        stored_device.connected = value
    db.session.commit()


def set_stored_devices_recording_setting(stored_devices, value):
    for stored_device in stored_devices:
        stored_device.recording = value
    db.session.commit()


def delete_stored_devices(stored_devices):
    for stored_device in stored_devices:
        db.session.delete(stored_device)
    db.session.commit()


def store_unique_time_data(table_column,
                           parent_id,
                           data_to_check,
                           id_to_check,
                           data_to_add):
    # See if the date item (year, month, etc) is already stored
    table_data = data_to_add.__class__.query.filter(
        table_column == data_to_check).filter(
            parent_id == id_to_check).first()
    # If the it is not stored...
    if not table_data:
        # ...store the data
        db.session.add(data_to_add)
        db.session.commit()
        # ...and query it again to get its id
        table_data = data_to_add.__class__.query.filter(
            table_column == data_to_check).first()
    return table_data


def get_correct_hour_id_to_link_to_measured_data(time_now):
    year_data = store_unique_time_data(
        table_column=Year.year,
        parent_id=None,
        data_to_check=time_now.year,
        id_to_check=None,
        data_to_add=Year(year=time_now.year)
    )
    month_data = store_unique_time_data(
        table_column=Month.month,
        parent_id=Month.year_id,
        data_to_check=time_now.month,
        id_to_check=year_data.id,
        data_to_add=Month(month=time_now.month,
                          year_id=year_data.id)
    )
    day_data = store_unique_time_data(
        table_column=Day.day,
        parent_id=Day.month_id,
        data_to_check=time_now.day,
        id_to_check=month_data.id,
        data_to_add=Day(day=time_now.day,
                        month_id=month_data.id)
    )
    hour_data = store_unique_time_data(
        table_column=Hour.hour,
        parent_id=Hour.day_id,
        data_to_check=time_now.hour,
        id_to_check=day_data.id,
        data_to_add=Hour(hour=time_now.hour,
                         day_id=day_data.id)
    )
    return hour_data.id

def delete_excess_data():
    max_hour_id = db.session.query(Hour).order_by(Hour.id.desc()).first().id
    with open("./appsettings.json") as f:
        settings_data = json.load(f)
        f.close()
    hours_to_delete = db.session.query(Hour).filter(
        Hour.id < (max_hour_id - settings_data["hours to store [h]"])).all()
    for hour in hours_to_delete:
        db.session.delete(hour)
    db.session.commit()

def store_measured_data(data, time_now, device_id, hour_id):
    # has keyerror when n
    new_data = Roomdata(
        temperature=data['variables']['temperature']
        if 'temperature' in data['variables'].keys() else None,
        humidity=data['variables']['humidity']
        if 'humidity' in data['variables'].keys() else None,
        movement_detection=data['variables']['movementDetected']
        if 'movementDetected' in data['variables'].keys() else None,
        date=time_now,
        device_id=device_id,
        hour_id=hour_id)
    db.session.add(new_data)
    if new_data.movement_detection == 1:
        hour = db.session.query(Hour).filter_by(id=hour_id).first()
        hour.movement_detection = 1
    db.session.commit()


def get_data_for_recording_device(sample_period_hours,
                                  start_date, device: DB_Device):
    delete_excess_data()
    data = []
    first_date_to_consider = db.session.query(Roomdata).filter(
        Roomdata.date >= start_date).order_by(Roomdata.id.asc()).first()
    if first_date_to_consider:
        hours_to_consider = Hour.query.filter(
            Hour.id >= first_date_to_consider.hour_id).all()
        if sample_period_hours != 0:
            hour_count = 0
            for hour in hours_to_consider:
                hour_count += 1
                if not hour_count % sample_period_hours:
                    roomdata = db.session.query(Roomdata).with_parent(
                        hour).with_parent(device).first()
                    if roomdata:
                        roomdata.movement_detection = hour.movement_detection
                        data.append(roomdata)
        else:
            data += db.session.query(Roomdata).with_parent(device).filter(
                Roomdata.date >= start_date).limit(1000).all()
    return data


def get_data_for_recording_devices(sample_period_hours, retrieval_start_date):
    recording_devices = get_stored_devices_to_be_monitored()
    results_dict = {}
    for recording_device in recording_devices:
        results_dict.update({recording_device.name:
                            get_data_for_recording_device(
                                sample_period_hours=sample_period_hours,
                                start_date=retrieval_start_date,
                                device=recording_device)})
    return results_dict, recording_devices
