import re


def extraer_datos_zabbix(page_content):
    # Patrones de expresiones regulares para extraer los valores
    patterns = {
        'serial.number': r"Tag (\d+) - Station EC-(\w+)",
        'media.site1': r"MEDIA site 1 crc=0x\w+ (?:IN USE state: ACTIVE|IN USE state: READY|RESERVE state: \w+)  "
                       r"capacity=\d+\.?\d*Mb  free=(\d+\.\d+)%",
        'media.site2': r"MEDIA site 2 crc=0x\w+ (?:IN USE state: ACTIVE|IN USE state: READY|RESERVE state: \w+)  "
                       r"capacity=\d+\.?\d*Mb  free=(\d+\.\d+)%",
        'q330.serial': r"Q330 Serial Number: (.+)",
        'clock.quality': r"Clock Quality: (\d+)%",
        'input.voltage': r"Input Voltage: (\d+\.\d+)V",
        'system.temp': r"System Temperature: (\d+)C",
        'main.current': r"Main Current: (\d+)ma",
        'sat.used': r"Sat. Used: (\d+)"
    }

    data = {}

    # Buscar los patrones en el contenido y guardar los valores en el diccionario 'data'
    for key, pattern in patterns.items():
        match = re.search(pattern, page_content)
        if match:
            if key == 'serial.number':
                data['serial.number'] = match.group(1)
                data['station.code'] = match.group(2)
            elif key == 'media.site1' or key == 'media.site2':
                space_free = float(match.group(1))
                space_total = 100.0  # Supongamos que el espacio total es 100
                space_occupied = space_total - space_free
                data[key + '.space.occupied'] = space_occupied
            else:
                data[key] = match.group(1)
        else:
            data[key] = None
    print(f"XXXXXXXXX {data}")
    return data