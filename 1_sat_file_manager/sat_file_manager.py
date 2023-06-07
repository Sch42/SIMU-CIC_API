# -*- coding: utf-8 -*-
"""
Created on Wed Mar  8 14:02:29 2023

@author: Sacha
"""
import datetime as dt
import os
from pathlib import Path


from datetime import datetime, timedelta, timezone

class File():
    
    def __init__(self, filepath : str) -> None:
        """
        This class aims at ensuring the validity of a given filepath as while
        enabling one to easily extract information related to the said filepath

        Parameters
        ----------
        filepath : str
            Sat_DISTANCE_GROUND_STATION_1.txt

        Raises
        ------
        ValueError
            - filepath cannot be empty.
            - filepath cannot be empty or consist only of whitespace characters.
        TypeError
            - filepath must be a string.
            - extension must be '.txt'.
        FileNotFoundError
            - filepath should exists

        Returns
        -------
        None

        """
        if not filepath:
            raise ValueError("filepath cannot be empty.")
        if not isinstance(filepath, str):
            raise TypeError("filepath must be a string.")
        elif filepath.strip() == "":
            raise ValueError("filepath cannot consist only of whitespace characters.")
        elif any(ord(character) >= 128 for character in filepath):
            raise TypeError("filepath cannot contain non-ASCII characters.")
        elif Path(filepath).suffix != ".txt":
            raise ValueError("filepath extension must be '.txt'.")
        elif not os.path.exists(filepath):
            raise FileNotFoundError("filepath should exists.")
        self.filepath = filepath
    
    def get_dirname(self) -> str:
        return os.path.dirname(self.filepath)
    
    def get_basename(self) -> str:
        return os.path.basename(self.filepath)
    
    def get_extension(self) -> str:
        return Path(self.filepath).suffix

VALID_FILENAMES = ["Sat_DISTANCE_GROUND_STATION_1.txt", "Sat_DISTANCE_GROUND_STATION_2.txt",
                   "Sat_ORBIT_NUMBER.txt", "Sat_SATELLITE_DIRECTION-GROUND_STATION_1_FRAME.txt",
                   "Sat_SATELLITE_DIRECTION-GROUND_STATION_2_FRAME.txt",
                   "Sat_SATELLITE_ALTITUDE.txt", "Sat_SATELLITE_ECLIPSE.txt",
                   "Sat_GEOMETRICAL_VISIBILITY_GROUND_STATION_1.txt",
                   "Sat_GEOGRAPHICAL_COORDINATES.txt",
                   "Sat_SATELLITE_ALTITUDE.txt"]

class File_Parser(File):
    
    def __init__(self, filepath : str) -> None:
        """
        This class aims at processing the Sat files generated by the simu-cic
        software (https://www.connectbycnes.fr/simu-cic).
        
        Parameters
        ----------
        filepath : str
            Sat_DISTANCE_GROUND_STATION_1.txt

        Raises
        ------
        ValueError
            The filename must be in {VALID_FILENAMES} (see SIMU-CIC_User_Manual).

        Returns
        -------
        None

        """
        super().__init__(filepath)
        if self.get_basename() not in VALID_FILENAMES:
            raise ValueError(f"The filename must be in {VALID_FILENAMES}.")
        self.simulation_data = self.get_simulation_data()
        
    def get_simulation_informations(self, file : File) -> dict:
        """
        Extracts useful informations from the given file.

        Parameters
        ----------
        file : File
            File(Sat_DISTANCE_GROUND_STATION_1.txt)

        Returns
        -------
        dict
            {'CIC_MEM_VERS': '2.0', 'CREATION_DATE': '2021-06-23T09:52:26.000', 
            'ORIGINATOR': 'CNES', 'COMMENT': 'days (MJD), sec (UTC), distance (km)', 
            'OBJECT_NAME': 'Sat', 'OBJECT_ID': 'Sat', 'USER_DEFINED_PROTOCOL': 'CIC', 
            'USER_DEFINED_CONTENT': 'DISTANCE_GROUND_STATION_1', 'TIME_SYSTEM': 'UTC', 
            'START_TIME': '2021-06-22T00:00:00.000', 'STOP_TIME': '2022-06-22T00:00:00.000'}

        """
        simulation_informations = {}
        line = file.readline()
        while len(line) > 0:
            line = line.strip()
            if line == 'META_STOP':
                break
            line_datas = line.split(' = ')
            if len(line_datas) == 2:
                line_datas
                key, value = line_datas
                simulation_informations[key.strip()] = value.strip()
            line = file.readline()
        return simulation_informations
    
    def set_str_to_datetime(self, str_date : str) -> dt.datetime:
        """
        Convert date given in str to datetime.

        Parameters
        ----------
        str_date : str
            2021-06-22T00:00:00.000'

        Returns
        -------
        dt.datetime
            dt.datetime(2021, 6, 22, 0, 0)

        """
        return dt.datetime.strptime(str_date, '%Y-%m-%dT%H:%M:%S.%f')
    
    def format_simulation_informations(self, simulation_informations : dict) -> dict:
        """
        Parse/format the given simulation informations.

        Parameters
        ----------
        simulation_informations : dict
            {'CIC_MEM_VERS': '2.0', 'CREATION_DATE': '2021-06-23T09:52:26.000', 
            'ORIGINATOR': 'CNES', 'COMMENT': 'days (MJD), sec (UTC), distance (km)', 
            'OBJECT_NAME': 'Sat', 'OBJECT_ID': 'Sat', 'USER_DEFINED_PROTOCOL': 'CIC', 
            'USER_DEFINED_CONTENT': 'DISTANCE_GROUND_STATION_1', 'TIME_SYSTEM': 'UTC', 
            'START_TIME': '2021-06-22T00:00:00.000', 'STOP_TIME': '2022-06-22T00:00:00.000'}

        Returns
        -------
        dict
            {'CIC_MEM_VERS': '2.0', 'CREATION_DATE': dt.datetime(2021, 6, 23, 9, 52, 26), 
            'ORIGINATOR': 'CNES', 'COMMENT': ['Date', 'distance (km)'], 
            'OBJECT_NAME': 'Sat', 'OBJECT_ID': 'Sat', 'USER_DEFINED_PROTOCOL': 'CIC', 
            'USER_DEFINED_CONTENT': 'DISTANCE_GROUND_STATION_1', 'TIME_SYSTEM': 'UTC', 
            'START_TIME': dt.datetime(2021, 6, 22, 0, 0), 'STOP_TIME': dt.datetime(2022, 6, 22, 0, 0)}

        """
        comment = simulation_informations['COMMENT']
        comment = comment.split(',')
        comment = [x.strip() for x in comment]
        comment[:2] = ['Date']
        simulation_informations['COMMENT'] = comment
        simulation_informations['CREATION_DATE'] = self.set_str_to_datetime(simulation_informations['CREATION_DATE'])
        simulation_informations['START_TIME'] = self.set_str_to_datetime(simulation_informations['START_TIME'])
        simulation_informations['STOP_TIME'] = self.set_str_to_datetime(simulation_informations['STOP_TIME'])
        return simulation_informations
    
    def get_simulation_results(self, file : File)  -> list:
        """
        Extracts the simulation results from the given file.

        Parameters
        ----------
        file : File
            File(Sat_DISTANCE_GROUND_STATION_1.txt)

        Returns
        -------
        list
            [['59409', '1020.00000', '1096.411'], 
            ['59409', '1030.00000', '1052.271'], 
            ['59409', '1040.00000', '1010.944']]

        """
        line = file.readline()
        simulation_results = []
        while len(line) > 0:
            if line != '\n':
                line = line.strip().split()
                simulation_results.append(line)
            line = file.readline()
        return simulation_results
    
    def set_mjd_to_datetime(self, days : int) -> dt.datetime:
        """
        Convert date given in Modified Julian Day (mjd) to datetime.

        Parameters
        ----------
        days : int
            58931

        Returns
        -------
        dt.datetime
            dt.datetime(2020, 3, 23, 0, 0, tzinfo=dt.timezone.utc)

        """
        mjd = (datetime(1858, 11, 17, tzinfo=timezone.utc) 
                + timedelta(days = days))
        return mjd
    
    def set_sec_to_datetime(self, sec : float) -> dt.datetime:
        """
        Convert seconds given in float to datetime.

        Parameters
        ----------
        days : float
            0

        Returns
        -------
        dt.datetime
            dt.timedelta(0)

        """
        sec = timedelta(seconds = sec)
        return sec
    
    def format_simulation_results(self, simulation_results : list) -> list:
        """
        Parse/format the given simulation results.

        Parameters
        ----------
        simulation_results : list
            [['59409', '1020.00000', '1096.411'], 
            ['59409', '1030.00000', '1052.271'], 
            ['59409', '1040.00000', '1010.944']]

        Returns
        -------
        list
            [[dt.datetime(2021, 7, 14, 0, 17, tzinfo=dt.timezone.utc), 1096.411], 
            [dt.datetime(2021, 7, 14, 0, 17, 10, tzinfo=dt.timezone.utc), 1052.271], 
            [dt.datetime(2021, 7, 14, 0, 17, 20, tzinfo=dt.timezone.utc), 1010.944]]

        """
        for index, simulation_result in enumerate(simulation_results):
            simulation_result = list(map(float, simulation_result))
            mjd = self.set_mjd_to_datetime(simulation_result[0])
            sec = self.set_sec_to_datetime(simulation_result[1])
            simulation_result[:2] = [mjd + sec]
            simulation_results[index] = simulation_result
        return simulation_results
    
    def get_simulation_data(self) -> dict:
        """
        Combine simulation informations with simulation results.

        Returns
        -------
        dict
            {'CIC_MEM_VERS': '2.0', 'CREATION_DATE': dt.datetime(2021, 6, 23, 9, 52, 26), 
            'ORIGINATOR': 'CNES', 'COMMENT': ['Date', 'distance (km)'], 'OBJECT_NAME': 'Sat', 
            'OBJECT_ID': 'Sat', 'USER_DEFINED_PROTOCOL': 'CIC', 
            'USER_DEFINED_CONTENT': 'DISTANCE_GROUND_STATION_1', 'TIME_SYSTEM': 'UTC', 
            'START_TIME': dt.datetime(2021, 6, 22, 0, 0), 'STOP_TIME': dt.datetime(2022, 6, 22, 0, 0), 
            'SIMULATION_RESULTS': [[dt.datetime(2021, 7, 14, 0, 17, tzinfo=dt.timezone.utc), 1096.411], 
                                   [dt.datetime(2021, 7, 14, 0, 17, 10, tzinfo=dt.timezone.utc), 1052.271], 
                                   [dt.datetime(2021, 7, 14, 0, 17, 20, tzinfo=dt.timezone.utc), 1010.944]]}

        """
        with open(self.filepath) as file:
            simulation_informations = self.get_simulation_informations(file)
            simulation_informations = self.format_simulation_informations(simulation_informations)
            simulation_results = self.get_simulation_results(file)
            simulation_results = self.format_simulation_results(simulation_results) 
            simulation_data = simulation_informations
            simulation_data['SIMULATION_RESULTS'] = simulation_results
        return simulation_data
    
    def get_simulation_result_date(self, index):
        return self.get_results()[index][0]
    
    def get_results(self):
        return self.simulation_data['SIMULATION_RESULTS']
    
    def get_version(self):
        return self.simulation_data['CIC_MEM_VERS']
    
    def get_creation_date(self):
        return self.simulation_data['CREATION_DATE']
    
    def get_originator(self):
        return self.simulation_data['ORIGINATOR']
    
    def get_comment(self):
        return self.simulation_data['COMMENT']
    
    def get_object_name(self):
        return self.simulation_data['OBJECT_NAME']
    
    def get_object_id(self):
        return self.simulation_data['OBJECT_ID']
    
    def get_user_defined_protocol(self):
        return self.simulation_data['USER_DEFINED_PROTOCOL']
    
    def get_user_defined_content(self):
        return self.simulation_data['USER_DEFINED_CONTENT']
    
    def get_time_system(self):
        return self.simulation_data['TIME_SYSTEM']
    
    def get_start_time(self):
        return self.simulation_data['START_TIME']
    
    def get_stop_time(self):
        return self.simulation_data['STOP_TIME']
    
class Sat_Orbit_Number(File_Parser):
    
    def __init__(self, path : str):
        """
        This class aims at extracting specific informations from Sat_ORBIT_NUMBER 
        files generated by the simu-cic software.

        Parameters
        ----------
        path : str
            Sat_ORBIT_NUMBER.txt

        """
        super().__init__(path)
        if self.get_basename() != "Sat_ORBIT_NUMBER.txt":
            raise ValueError("Path basename should be Sat_ORBIT_NUMBER.txt")
        
    def get_orbit_number(self, index : int) -> int:
        return int(self.get_results()[index][1])
    
class Sat_Position(File_Parser):
    
    def __init__(self, path : str):
        """
        This class aims at extracting specific informations from Sat_SATELLITE_DIRECTION 
        files generated by the simu-cic software.

        Parameters
        ----------
        path : str
            Sat_SATELLITE_DIRECTION-GROUND_STATION_1_FRAME.txt

        """
        super().__init__(path)
    
    def get_sat_azimut(self, index):
        return float(self.get_results()[index][1])
    
    def get_sat_elevation(self, index):
        return float(self.get_results()[index][2])
    
    
class Sat_Visibility(File_Parser):
    
    def __init__(self, path : str):
        """
        This class aims at extracting specific informations from ...
        files generated by the simu-cic software.

        Parameters
        ----------
        path : str
            ....txt

        """
        super().__init__(path)
    
    def get_sat_visibility(self, index):
        return self.get_results()[index][1]
    
class Sat_Distance_To_Ground_Station(File_Parser):
    
    def __init__(self, path : str):
        """
        This class aims at extracting specific informations from ...
        files generated by the simu-cic software.

        Parameters
        ----------
        path : str
            ....txt

        """
        super().__init__(path)
    
    def get_sat_distance_to_ground_station(self, index):
        return self.get_results()[index][1]*1e3
    
class Sat_Geographical_Coordinates(File_Parser):
    
    def __init__(self, path : str):
        """
        This class aims at extracting specific informations from ...
        files generated by the simu-cic software.

        Parameters
        ----------
        path : str
            ....txt

        """
        super().__init__(path)
        if self.get_basename() != "Sat_GEOGRAPHICAL_COORDINATES.txt":
            raise ValueError("Path basename should be Sat_GEOGRAPHICAL_COORDINATES.txt")
    
    def get_sat_longitude(self, index):
        return self.get_results()[index][1]
    
    def get_sat_latitude(self, index):
        return self.get_results()[index][2]
    
class Sat_Eclipse(File_Parser):
    
    def __init__(self, path : str):
        """
        This class aims at extracting specific informations from Sat_SATELLITE_ECLIPSE
        files generated by the simu-cic software.

        Parameters
        ----------
        path : str
            Sat_SATELLITE_ECLIPSE.txt

        """
        super().__init__(path)
        if self.get_basename() != "Sat_SATELLITE_ECLIPSE.txt":
            raise ValueError("Path basename should be Sat_SATELLITE_ECLIPSE.txt")
    
    def get_sun_eclipse(self, index):
        return self.get_results()[index][1]
    
class Sat_Altitude(File_Parser):
    
    def __init__(self, path : str):
        """
        This class aims at extracting specific informations from Sat_SATELLITE_ALTITUDE.txt
        files generated by the simu-cic software.

        Parameters
        ----------
        path : str
            ....txt

        """
        super().__init__(path)
        if self.get_basename() != "Sat_SATELLITE_ALTITUDE.txt":
            raise ValueError("Path basename should be Sat_SATELLITE_ALTITUDE.txt")
    
    def get_sat_altitude(self, index):
        return self.get_results()[index][1]*1e3
    
