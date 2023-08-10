import re


def extraer_datos_zabbix(page_content):
    # Expresiones regulares para extraer los valores
    tag_pattern = r"Tag (\d+) - Station EC-(\w+)"
    media_site1_pattern = r"MEDIA site 1 crc=0x\w+ (?:IN USE state: ACTIVE|IN USE state: READY|RESERVE state: \w+)  capacity=\d+\.?\d*Mb  free=(\d+\.\d+)%"
    media_site2_pattern = r"MEDIA site 2 crc=0x\w+ (?:IN USE state: ACTIVE|IN USE state: READY|RESERVE state: \w+)  capacity=\d+\.?\d*Mb  free=(\d+\.\d+)%"
    q330_serial_pattern = r"Q330 Serial Number: (.+)"
    clock_quality_pattern = r"Clock Quality: (\d+)%"
    input_voltage_pattern = r"Input Voltage: (\d+\.\d+)V"
    system_temp_pattern = r"System Temperature: (\d+)C"
    main_current_pattern = r"Main Current: (\d+)ma"
    sat_used_pattern = r"Sat. Used: (\d+)"

    # Buscar los patrones en el contenido
    tag_match = re.search(tag_pattern, page_content)
    media_site1_match = re.search(media_site1_pattern, page_content)
    media_site2_match = re.search(media_site2_pattern, page_content)
    q330_serial_match = re.search(q330_serial_pattern, page_content)
    clock_quality_match = re.search(clock_quality_pattern, page_content)
    input_voltage_match = re.search(input_voltage_pattern, page_content)
    system_temp_match = re.search(system_temp_pattern, page_content)
    main_current_match = re.search(main_current_pattern, page_content)
    sat_used_match = re.search(sat_used_pattern, page_content)

    # Obtener los valores y ponerlos en un diccionario
    data = {
        'serial.number': tag_match.group(1) if tag_match else None,
        'station.code': tag_match.group(2) if tag_match else None,
        'media.site1': media_site1_match.group(1) if media_site1_match else None,
        'media.site2': media_site2_match.group(1) if media_site2_match else None,
        'q330.serial': q330_serial_match.group(1) if q330_serial_match else None,
        'clock.quality': clock_quality_match.group(1) if clock_quality_match else None,
        'input.voltage': input_voltage_match.group(1) if input_voltage_match else None,
        'system.temp': system_temp_match.group(1) if system_temp_match else None,
        'main.current': main_current_match.group(1) if main_current_match else None,
        'sat.used': sat_used_match.group(1) if sat_used_match else None,
    }
    return data
