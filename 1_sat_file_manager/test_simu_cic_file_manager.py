# -*- coding: utf-8 -*-
"""
Created on Thu Mar  9 11:02:33 2023

@author: Sacha
"""
import datetime as dt
import os
import unittest

from collections import defaultdict
from datetime import datetime, timedelta, timezone
from unittest.mock import patch
from unittest.mock import MagicMock
from tempfile import TemporaryFile, NamedTemporaryFile, TemporaryDirectory
from pathlib import Path

from hypothesis import given, assume, strategies as st

from simu_cic_file_manager import File, Stations_Ref_File_Parser, Simu_Cic_Info_File_Parser, \
    Sat_File_Parser, Sat_Orbit_Number, Sat_Altitude, \
    Sat_Geographical_Coordinates, Sat_Distance_To_Ground_Station, Sat_Visibility, \
    Sat_Position, Sat_Eclipse

PATH_DATA = r'^[A-Za-z]:\\(?:[^\\/:*?"<>|\r\n]+\\)*[^\\/:*?"<>|\r\n]*$|^/$|^\\$|^\\.\\.\\(?:[\\/][^\\/:*?"<>|\r\n]+)*$|^[^\\/:*?"<>|\r\n]+(?:[\\/][^\\/:*?"<>|\r\n]+)*$'

class Test_File(unittest.TestCase):
    
    @staticmethod
    def _create_temp_filepath(suffix : str = ".txt") -> NamedTemporaryFile:
        """
        Creates a temporary filepath with .txt as extension by default

        Parameters
        ----------
        suffix : TYPE, optional
            DESCRIPTION. The default is ".txt" : str.

        Returns
        -------
        NamedTemporaryFile
            DESCRIPTION.

        """
        temp_filepath = NamedTemporaryFile(suffix = suffix, delete = True)
        return temp_filepath

    # @staticmethod
    # def _Delete_Temp_Filepath(temp_filepath):
    #     temp_filepath.close()

    # @staticmethod
    # def _Create_Temp_Dir():
    #     return TemporaryDirectory()

    # @staticmethod
    # def _Delete_Temp_Dir(temp_dir):
    #     temp_dir.cleanup()
        
    def test_init_raises_valueerror_when_given_none_as_filepath(self) -> None:
        with self.assertRaises(ValueError):
            File(None)
            
    def test_init_raises_valuerrror_when_given_an_empty_filepath(self) -> None:
        with self.assertRaises(ValueError):
            File("")
            
    @given(filepath = st.one_of(st.floats(), st.integers()))
    def test_init_raises_typeerror_when_given_a_non_string_filepath(self, filepath : str) -> None:
        assume(not isinstance(filepath, str) and filepath)
        with self.assertRaises(TypeError):
            File(filepath)
            
    @given(filepath = st.from_regex(PATH_DATA))
    def test_init_raises_typeerror_when_given_a_non_ascii_filepath(self, filepath : str) -> None:
        if any(ord(character) >= 128 for character in filepath):
            with self.assertRaises(TypeError):
                File(filepath)

    def test_init_raises_Vvalueerror_when_given_whitespaces_as_filepath(self) -> None:
        with self.assertRaises(ValueError):
            File("    ")
                    
    @given(suffix = st.one_of(st.just(".pdf"), st.just(".xls"), st.just(".py"), st.just(".docx")))
    def test_init_raises_valueerror_when_filepath_suffix_is_not_txt(self, suffix : str):
        with self._create_temp_filepath(suffix = suffix) as temp_filepath:
            with self.assertRaises(ValueError):
                File(temp_filepath.name)
            
        # with MagicMock(name = "pathlib.Path") as mock_path:
        #     mock_path_instance = mock_path.return_value
        #     mock_path_instance.suffix = ".not_txt"
        #     with self.assertRaises(ValueError):
        #         File("filename.not_txt")
                    
    @given(path = st.from_regex(PATH_DATA))
    def test_init_raises_filenotfounderror_when_filepath_does_not_exist(self, path : str):
        # Test that the File class cannot be instantiated with a filepath that does not exist
        assume(all(ord(character) < 128 for character in path))
        filepath = path + "filename.txt"
        with self.assertRaises(FileNotFoundError):
            File(filepath)
            
        with patch("os.path.exists", return_value = False):
            with self.assertRaises(FileNotFoundError):
                File("this_file_does_not_exists.txt")
        
    def test_init_with_a_valid_filepath(self) -> None:
        with self._create_temp_filepath() as temp_filepath:
            file = File(temp_filepath.name)
            self.assertIsInstance(file, File)
            self.assertEqual(file.filepath, temp_filepath.name)
            
        with patch("os.path.exists", return_value = True):
            self.assertIsInstance(file, File)
            self.assertEqual(file.filepath, temp_filepath.name)
            
    def test_get_dirname(self) -> None:
        with self._create_temp_filepath() as temp_filepath:
            file = File(temp_filepath.name)
            self.assertEqual(file.get_dirname(), os.path.dirname(temp_filepath.name))
        
        with patch("os.path.dirname") as mock_dirname:
            mock_dirname.return_value = "a_dirname"
            self.assertEqual(file.get_dirname(), "a_dirname")
            
    def test_get_basename(self) -> None:
        with NamedTemporaryFile(suffix = ".txt", delete = True) as temp_filepath:
            file = File(temp_filepath.name)
            self.assertEqual(file.get_basename(), os.path.basename(temp_filepath.name))
        
        with patch("os.path.basename") as mock_basename:
            mock_basename.return_value = "a_basename"
            self.assertEqual(file.get_basename(), "a_basename")
            
    def test_get_extension(self) -> None:
        with NamedTemporaryFile(suffix = ".txt", delete = True) as temp_filepath:
            file = File(temp_filepath.name)
            self.assertEqual(file.get_extension(), Path(temp_filepath.name).suffix)
        
        # with patch("pathlib.Path") as mock_extension:
        #     mock_extension_instance = mock_extension.return_value
        #     mock_extension_instance.suffix = ".txt"
        #     self.assertEqual(file.get_Extension(), ".txt")
        
    
        
class Test_Stations_Ref_File_Parser(unittest.TestCase):
            
    def test_init_raises_valueerror_when_given_an_invalid_filename(self) -> None:
        with NamedTemporaryFile(suffix = ".txt", delete = True) as temp_filepath:
            with self.assertRaises(ValueError):
                Stations_Ref_File_Parser(temp_filepath.name)
                
    def test_init_with_a_valid_path(self) -> None:
        assume(os.path.exists("Stations_ref.txt"))
        file_parser = Stations_Ref_File_Parser("Stations_ref.txt")
        self.assertIsInstance(file_parser, Stations_Ref_File_Parser)
        self.assertEqual(file_parser.filepath, "Stations_ref.txt")

    def setUp(self) -> None: 
        self.path = "Stations_ref.txt"
        self.file_parser = Stations_Ref_File_Parser(self.path)
        self.ground_stations_informations = {'Grasse': {'name': 'Grasse', 
                                                        'longitude': 6.9216, 
                                                        'latitude': 43.7546, 
                                                        'altitude': 1323.0}, 
                                             'Paris': {'name': 'Paris', 
                                                       'longitude': 2.351, 
                                                       'latitude': 48.856, 
                                                       'altitude': 30.0}}
        self.ground_stations_data = {'Grasse': {'name': 'Grasse', 
                                                        'longitude': 6.9216, 
                                                        'latitude': 43.7546, 
                                                        'altitude': 1323.0}, 
                                    'Paris': {'name': 'Paris', 
                                              'longitude': 2.351, 
                                              'latitude': 48.856, 
                                              'altitude': 30.0}}
        
    def test_get_ground_stations_informations(self) -> None:
        with open(self.path) as file:
            self.assertEqual(self.file_parser.get_ground_stations_informations(file), 
                             self.ground_stations_informations)
        
    def test_get_ground_stations_data(self) -> None:
        self.assertEqual(self.file_parser.get_ground_stations_data(), 
                         self.ground_stations_data)
    
    def test_get_ground_station(self) -> None:
        self.assertEqual(self.file_parser.get_ground_station("Grasse"), 
                         {'name': 'Grasse', 'longitude': 6.9216, 'latitude': 43.7546, 
                          'altitude': 1323.0})
    
    def test_get_ground_longitude(self) -> None:
        self.assertEqual(self.file_parser.get_ground_station_longitude("Grasse"), 6.9216)

    def test_get_ground_latitude(self) -> None:
        self.assertEqual(self.file_parser.get_ground_station_latitude("Grasse"), 43.7546)
    
    def test_get_ground_altitude(self) -> None:
        self.assertEqual(self.file_parser.get_ground_station_altitude("Grasse"), 1323.0)
            
    
        
    
        
class Test_Simu_Cic_Info_File_Parser(unittest.TestCase):
            
    def test_init_raises_valueerror_when_given_an_invalid_filename(self) -> None:
        with NamedTemporaryFile(suffix = ".txt", delete = True) as temp_filepath:
            with self.assertRaises(ValueError):
                Simu_Cic_Info_File_Parser(temp_filepath.name)
                
    def test_init_with_a_valid_path(self) -> None:
        assume(os.path.exists("simu_cic_info.txt"))
        file_parser = Simu_Cic_Info_File_Parser("simu_cic_info.txt")
        self.assertIsInstance(file_parser, Simu_Cic_Info_File_Parser)
        self.assertEqual(file_parser.filepath, "simu_cic_info.txt")

    def setUp(self) -> None: 
        self.path = "simu_cic_info.txt"
        self.file_parser = Simu_Cic_Info_File_Parser(self.path)
        self.simulation_informations = defaultdict(list, 
                                                   {"Simulation synthesis": {"Simulation name": "simu", 
                                                                             "Start (UTC)": "2021/01/01 00:00:00.000", 
                                                                             "End (UTC)": "2021/01/02 00:00:00.000"}, 
                                                    "Satellite 1": {"Name": "Sat"}, 
                                                    "Initial conditions": {"Date (UTC)": "2021/01/01 00:00:00.000", 
                                                                           "Altitude (km)": "607.942", 
                                                                           "Eccentricity": "0.0023903", 
                                                                           "Inclination (deg)": "97.815", 
                                                                           "Argument of perigee (deg)": "118.055", 
                                                                           "Mean local time of ascending node (h)": "1.000", 
                                                                           "Argument of latitude (deg)": "24.699", 
                                                                           "Mean J2 orbital period (h)": "1.615"}, 
                                                    "Stations": {"1": "Grasse", "2": "Paris"}})
        self.formatted_simulation_informations = defaultdict(list, 
                                                               {"Simulation synthesis": {"Simulation name": "simu", 
                                                                                         "Start (UTC)": dt.datetime(2021, 1, 1, 0, 0), 
                                                                                         "End (UTC)": dt.datetime(2021, 1, 2, 0, 0)}, 
                                                                "Satellite 1": {"Name": "Sat"}, 
                                                                "Initial conditions": {"Date (UTC)": dt.datetime(2021, 1, 1, 0, 0), 
                                                                                       "Altitude (km)": "607.942", 
                                                                                       "Eccentricity": "0.0023903", 
                                                                                       "Inclination (deg)": "97.815", 
                                                                                       "Argument of perigee (deg)": "118.055", 
                                                                                       "Mean local time of ascending node (h)": "1.000", 
                                                                                       "Argument of latitude (deg)": "24.699", 
                                                                                       "Mean J2 orbital period (h)": "1.615"}, 
                                                                "Stations": {"1": "Grasse", "2": "Paris"}})
        self.simulation_data = defaultdict(list, 
                                           {"Simulation synthesis": {"Simulation name": "simu", 
                                                                     "Start (UTC)": dt.datetime(2021, 1, 1, 0, 0), 
                                                                     "End (UTC)": dt.datetime(2021, 1, 2, 0, 0)}, 
                                            "Satellite 1": {"Name": "Sat"}, 
                                            "Initial conditions": {"Date (UTC)": dt.datetime(2021, 1, 1, 0, 0), 
                                                                   "Altitude (km)": 607.942, 
                                                                   "Eccentricity": 0.0023903, 
                                                                   "Inclination (deg)": 97.815, 
                                                                   "Argument of perigee (deg)": 118.055, 
                                                                   "Mean local time of ascending node (h)": 1.0, 
                                                                   "Argument of latitude (deg)": 24.699, 
                                                                   "Mean J2 orbital period (h)": 1.615}, 
                                            "Stations": {"1": "Grasse", "2": "Paris"}})
        
    def test_set_str_to_datetime(self) -> None:
        self.assertEqual(self.file_parser.set_str_to_datetime("2021/01/01 00:00:00.000"), 
                        dt.datetime(2021, 1, 1, 0, 0))
        
    def test_get_simulation_informations(self) -> None:
        with open(self.path) as file:
            self.assertEqual(self.file_parser.get_simulation_informations(file), 
                             self.simulation_informations)
            
    def test_format_simulation_informations(self) -> None:
        self.assertEqual(self.file_parser.format_simulation_informations(self.simulation_informations), 
                         self.formatted_simulation_informations)
                         
    def test_get_simulation_data(self) -> None:
        self.assertEqual(self.file_parser.get_simulation_data(), 
                          self.simulation_data)
        
    def test_get_simulation_synthesis(self) -> None:
        self.assertEqual(self.file_parser.get_simulation_synthesis(), 
                          {"Simulation name": "simu",
                          "Start (UTC)": dt.datetime(2021, 1, 1, 0, 0), 
                          "End (UTC)": dt.datetime(2021, 1, 2, 0, 0)})
         
    def test_get_simulation_name(self) -> None:
        self.assertEqual(self.file_parser.get_simulation_name(), "simu")
         
    def test_get_simulation_start(self) -> None:
        self.assertEqual(self.file_parser.get_simulation_start(), dt.datetime(2021, 1, 1, 0, 0))
         
    def test_get_simulation_stop(self) -> None:
        self.assertEqual(self.file_parser.get_simulation_stop(), dt.datetime(2021, 1, 2, 0, 0))
        
    def test_get_satellite_name(self) -> None:
        self.assertEqual(self.file_parser.get_satellite_name(), "Sat")
        
    def test_get_initial_conditions(self) -> None:
        self.assertEqual(self.file_parser.get_initial_conditions(), 
                          {"Date (UTC)": dt.datetime(2021, 1, 1, 0, 0), 
                        "Altitude (km)": 607.942, 
                        "Eccentricity": 0.0023903, 
                        "Inclination (deg)": 97.815, 
                        "Argument of perigee (deg)": 118.055, 
                        "Mean local time of ascending node (h)": 1.0, 
                        "Argument of latitude (deg)": 24.699, 
                        "Mean J2 orbital period (h)": 1.615})
                        
    def test_get_initial_conditions_date(self) -> None:
        self.assertEqual(self.file_parser.get_initial_conditions_date(), 
                          dt.datetime(2021, 1, 1, 0, 0))
                         
    def test_get_initial_conditions_altitude(self) -> None:
        self.assertEqual(self.file_parser.get_initial_conditions_altitude(), 607.942)
                     
    def test_get_initial_conditions_eccentricity(self) -> None:
        self.assertEqual(self.file_parser.get_initial_conditions_eccentricity(),  0.0023903)
                     
    def test_get_initial_conditions_inclination(self) -> None:
        self.assertEqual(self.file_parser.get_initial_conditions_inclination(),  97.815)
                     
    def test_get_initial_conditions_argument_of_perigee(self) -> None:
        self.assertEqual(self.file_parser.get_initial_conditions_argument_of_perigee(),  118.055)
                     
    def test_get_initial_conditions_mltan(self) -> None:
        self.assertEqual(self.file_parser.get_initial_conditions_mltan(),  1.0)
                     
    def test_get_initial_conditions_argument_of_latitude(self) -> None:
        self.assertEqual(self.file_parser.get_initial_conditions_argument_of_latitude(),  24.699)
                     
    def test_get_initial_conditions_mean_j2_orbital_period(self) -> None:
        self.assertEqual(self.file_parser.get_initial_conditions_mean_j2_orbital_period(), 1.615)
        
VALID_FILENAMES = ["Sat_DISTANCE_GROUND_STATION_1.txt", "Sat_DISTANCE_GROUND_STATION_2.txt",
                    "Sat_ORBIT_NUMBER.txt", "Sat_SATELLITE_DIRECTION-GROUND_STATION_1_FRAME.txt",
                    "Sat_SATELLITE_DIRECTION-GROUND_STATION_2_FRAME.txt",
                    "Sat_SATELLITE_ALTITUDE.txt", "Sat_SATELLITE_ECLIPSE.txt",
                    "Sat_GEOMETRICAL_VISIBILITY_GROUND_STATION_1.txt",
                    "Sat_GEOGRAPHICAL_COORDINATES.txt",
                    "Sat_SATELLITE_ALTITUDE.txt"]

class Test_Sat_File_Parser(unittest.TestCase):
            
    def test_init_raises_valueerror_when_given_an_invalid_filename(self) -> None:
        with NamedTemporaryFile(suffix = ".txt", delete = True) as temp_filepath:
            if temp_filepath.name not in VALID_FILENAMES:
                with self.assertRaises(ValueError):
                    Sat_File_Parser(temp_filepath.name)
                    
    @given(filename = st.sampled_from(VALID_FILENAMES))
    def test_init_with_a_valid_path(self, filename : str) -> None:
        assume(os.path.exists(filename))
        file_parser = Sat_File_Parser(filename)
        self.assertIsInstance(file_parser, Sat_File_Parser)
        self.assertEqual(file_parser.filepath, filename)
        
    def setUp(self) -> None: 
        self.path = "Sat_DISTANCE_GROUND_STATION_1.txt"
        self.file_parser = Sat_File_Parser(self.path)
        self.simulation_informations ={"CIC_MEM_VERS": "2.0", "CREATION_DATE": "2021-06-23T09:52:26.000", 
                                        "ORIGINATOR": "CNES", "COMMENT": "days (MJD), sec (UTC), distance (km)", 
                                        "OBJECT_NAME": "Sat", "OBJECT_ID": "Sat", "USER_DEFINED_PROTOCOL": "CIC", 
                                        "USER_DEFINED_CONTENT": "DISTANCE_GROUND_STATION_1", "TIME_SYSTEM": "UTC", 
                                        "START_TIME": "2021-06-22T00:00:00.000", "STOP_TIME": "2022-06-22T00:00:00.000"}
        self.formatted_simulation_informations = {"CIC_MEM_VERS": "2.0", "CREATION_DATE": dt.datetime(2021, 6, 23, 9, 52, 26), 
                                                "ORIGINATOR": "CNES", "COMMENT": ["Date", "distance (km)"], 
                                                "OBJECT_NAME": "Sat", "OBJECT_ID": "Sat", "USER_DEFINED_PROTOCOL": "CIC", 
                                                "USER_DEFINED_CONTENT": "DISTANCE_GROUND_STATION_1", "TIME_SYSTEM": "UTC", 
                                                "START_TIME": dt.datetime(2021, 6, 22, 0, 0), "STOP_TIME": dt.datetime(2022, 6, 22, 0, 0)}
        self.simulation_results = [["59409", "1020.00000", "1096.411"], 
                                    ["59409", "1030.00000", "1052.271"], 
                                    ["59409", "1040.00000", "1010.944"]]
        self.formatted_simulation_results = [[dt.datetime(2021, 7, 14, 0, 17, tzinfo=dt.timezone.utc), 1096.411], 
                                          [dt.datetime(2021, 7, 14, 0, 17, 10, tzinfo=dt.timezone.utc), 1052.271], 
                                          [dt.datetime(2021, 7, 14, 0, 17, 20, tzinfo=dt.timezone.utc), 1010.944]]
        self.simulation_data = {"CIC_MEM_VERS": "2.0", "CREATION_DATE": dt.datetime(2021, 6, 23, 9, 52, 26), 
                                "ORIGINATOR": "CNES", "COMMENT": ["Date", "distance (km)"], "OBJECT_NAME": "Sat", 
                                "OBJECT_ID": "Sat", "USER_DEFINED_PROTOCOL": "CIC", 
                                "USER_DEFINED_CONTENT": "DISTANCE_GROUND_STATION_1", "TIME_SYSTEM": "UTC", 
                                "START_TIME": dt.datetime(2021, 6, 22, 0, 0), "STOP_TIME": dt.datetime(2022, 6, 22, 0, 0), 
                                "SIMULATION_RESULTS": [[dt.datetime(2021, 7, 14, 0, 17, tzinfo=dt.timezone.utc), 1096.411], 
                                                        [dt.datetime(2021, 7, 14, 0, 17, 10, tzinfo=dt.timezone.utc), 1052.271], 
                                                        [dt.datetime(2021, 7, 14, 0, 17, 20, tzinfo=dt.timezone.utc), 1010.944]]}
        self.simulation_result_date = dt.datetime(2021, 7, 14, 0, 17, tzinfo=dt.timezone.utc)
        
    def test_get_simulation_informations(self) -> None:
        with open(self.path) as file:
            self.assertEqual(self.file_parser.get_simulation_informations(file), self.simulation_informations)
    
    def test_set_str_to_datetime(self) -> None:
        value = dt.datetime(2021, 6, 23, 9, 52, 26)
        self.assertEqual(self.file_parser.set_str_to_datetime("2021-06-23T09:52:26.000"), value)
        
        # with patch("datetime.datetime") as  mock_extension:
        #     mock_extension_instance = mock_extension.return_value
        #     mock_extension_instance.strptime = "a_dirname"
        #     self.assertEqual(self.file_parser.set_str_to_datetime("2021-06-23T09:52:26.000"), value)

    def test_format_simulation_informations(self) -> None:
        self.assertEqual(self.file_parser.format_simulation_informations(self.simulation_informations), self.formatted_simulation_informations)
        
    def test_get_simulation_results(self) -> None:
        with open(self.path) as f:
            self.file_parser.get_simulation_informations(f)
            self.assertEqual(self.file_parser.get_simulation_results(f), self.simulation_results)
                    
    def test_mjd_to_datetime(self) -> None:
        value = dt.datetime(2020, 3, 23, 0, 0, tzinfo=dt.timezone.utc)
        self.assertEqual(self.file_parser.set_mjd_to_datetime(58931), value)
        
    def test_sec_to_datetime(self) -> None:
        value = dt.timedelta(0)
        self.assertEqual(self.file_parser.set_sec_to_datetime(0.0), value)
                     
    def test_get_simulation_data(self) -> None:
        self.assertEqual(self.file_parser.get_simulation_data(), self.simulation_data)        
    
    def test_format_simulation_results(self) -> None:
        self.assertEqual(self.file_parser.format_simulation_results(self.simulation_results), self.formatted_simulation_results)
        
    def test_get_simulation_result_date(self) -> None:
        self.assertEqual(self.file_parser.get_simulation_result_date(0), self.simulation_result_date)
        
    def test_get_results(self) -> None:
        self.assertEqual(self.file_parser.get_results(), self.formatted_simulation_results)
    
    def test_get_version(self) -> None:
        self.assertEqual(self.file_parser.get_version(), "2.0")
    
    def test_get_creation_date(self) -> None:
        self.assertEqual(self.file_parser.get_creation_date(), dt.datetime(2021, 6, 23, 9, 52, 26))
    
    def test_get_originator(self) -> None:
        self.assertEqual(self.file_parser.get_originator(), "CNES")
    
    def test_get_comment(self) -> None:
        self.assertEqual(self.file_parser.get_comment(), ["Date", "distance (km)"])
    
    def test_get_object_name(self) -> None:
        self.assertEqual(self.file_parser.get_object_name(), "Sat")
    
    def test_get_object_id(self) -> None:
        self.assertEqual(self.file_parser.get_object_id(), "Sat")
    
    def test_get_user_defined_protocol(self) -> None:
        self.assertEqual(self.file_parser.get_user_defined_protocol(), "CIC")
    
    def test_get_user_defined_content(self) -> None:
        self.assertEqual(self.file_parser.get_user_defined_content(), "DISTANCE_GROUND_STATION_1")
    
    def test_get_time_system(self) -> None:
        self.assertEqual(self.file_parser.get_time_system(), "UTC")
    
    def test_get_start_time(self) -> None:
        self.assertEqual(self.file_parser.get_start_time(), dt.datetime(2021, 6, 22, 0, 0))
    
    def test_get_stop_time(self) -> None:
        self.assertEqual(self.file_parser.get_stop_time(), dt.datetime(2022, 6, 22, 0, 0))
        
        
class Test_Sat_Orbit_Number(unittest.TestCase):
    
    @given(path = st.sampled_from(VALID_FILENAMES))    
    def test_init_given_an_invalid_path(self, path):
        assume(os.path.exists(path))
        file = File(path)
        if file.get_basename() != "Sat_ORBIT_NUMBER.txt":
            with self.assertRaises(ValueError):
                Sat_Orbit_Number(path)
                
    def test_init_with_a_valid_path(self) -> None:
        path = "Sat_ORBIT_NUMBER.txt"
        self.assertIsInstance(Sat_Orbit_Number(path), Sat_Orbit_Number)
                
        
    def setUp(self):
        self.sat_orbit_number = Sat_Orbit_Number("Sat_ORBIT_NUMBER.txt")
        
    def test_get_orbit_number(self):
        self.assertEqual(self.sat_orbit_number.get_orbit_number(0), 329)

class Test_Sat_Position(unittest.TestCase):
                
    def test_init_with_a_valid_path(self) -> None:
        path = "Sat_SATELLITE_DIRECTION-GROUND_STATION_1_FRAME.txt"
        self.assertIsInstance(Sat_Position(path), Sat_Position)
        
    def setUp(self):
        self.sat_position = Sat_Position("Sat_SATELLITE_DIRECTION-GROUND_STATION_1_FRAME.txt")
        
    def test_get_sat_azimut(self):
        self.assertEqual(self.sat_position.get_sat_azimut(0), 202.04716)    
        
    def test_get_sat_elevation(self):
        self.assertEqual(self.sat_position.get_sat_elevation(0), 29.24913)  
        

class Test_Sat_Visibility(unittest.TestCase):
                
    def test_init_with_a_valid_path(self) -> None:
        path = "Sat_GEOMETRICAL_VISIBILITY_GROUND_STATION_1.txt"
        self.assertIsInstance(Sat_Position(path), Sat_Position)
        
    def setUp(self):
        self.sat_visibility = Sat_Visibility("Sat_GEOMETRICAL_VISIBILITY_GROUND_STATION_1.txt")
        
    def test_get_sat_visibility(self):
        self.assertEqual(self.sat_visibility.get_sat_visibility(0), 1)  

class Test_Sat_Distance_To_Ground_Station(unittest.TestCase):
                
    def test_init_with_a_valid_path(self) -> None:
        path = "Sat_DISTANCE_GROUND_STATION_1.txt"
        self.assertIsInstance(Sat_Distance_To_Ground_Station(path), Sat_Distance_To_Ground_Station)
        
    def setUp(self):
        self.sat_distance_to_groundstation = Sat_Distance_To_Ground_Station("Sat_DISTANCE_GROUND_STATION_1.txt")
        
    def test_get_sat_distance_to_ground_station(self):
        self.assertEqual(self.sat_distance_to_groundstation.get_sat_distance_to_ground_station(0), 1096411.0) 
        
class Test_Sat_Geographical_Coordinates(unittest.TestCase):
    
    @given(path = st.sampled_from(VALID_FILENAMES))    
    def test_init_given_an_invalid_path(self, path):
        assume(os.path.exists(path))
        file = File(path)
        if file.get_basename() != "Sat_GEOGRAPHICAL_COORDINATES.txt":
            with self.assertRaises(ValueError):
                Sat_Geographical_Coordinates(path)
                
    def test_init_with_a_valid_path(self) -> None:
        path = "Sat_GEOGRAPHICAL_COORDINATES.txt"
        self.assertIsInstance(Sat_Geographical_Coordinates(path), Sat_Geographical_Coordinates)
                
    def setUp(self):
        self.sat_geographical_coordinates = Sat_Geographical_Coordinates("Sat_GEOGRAPHICAL_COORDINATES.txt")
        
    def test_get_sat_longitude(self):
        self.assertEqual(self.sat_geographical_coordinates.get_sat_longitude(0), 358.419329)
        
    def test_get_sat_latitude(self):
        self.assertEqual(self.sat_geographical_coordinates.get_sat_latitude(0), 41.469732)

class Test_Sat_Eclipse(unittest.TestCase):
    
    @given(path = st.sampled_from(VALID_FILENAMES))    
    def test_init_given_an_invalid_path(self, path):
        assume(os.path.exists(path))
        file = File(path)
        if file.get_basename() != "Sat_SATELLITE_ECLIPSE.txt":
            with self.assertRaises(ValueError):
                Sat_Eclipse(path)
                
    def test_init_with_a_valid_path(self) -> None:
        path = "Sat_SATELLITE_ECLIPSE.txt"
        self.assertIsInstance(Sat_Eclipse(path), Sat_Eclipse)
                
    def setUp(self):
        self.sat_eclipse = Sat_Eclipse("Sat_SATELLITE_ECLIPSE.txt")
        
    def test_get_orbit_number(self):
        self.assertEqual(self.sat_eclipse.get_sun_eclipse(0), 100.0)
        
class Test_Sat_Altitude(unittest.TestCase):
    
    @given(path = st.sampled_from(VALID_FILENAMES))    
    def test_init_given_an_invalid_path(self, path):
        assume(os.path.exists(path))
        file = File(path)
        if file.get_basename() != "Sat_SATELLITE_ALTITUDE.txt":
            with self.assertRaises(ValueError):
                Sat_Altitude(path)
                
    def test_init_with_a_valid_path(self) -> None:
        path = "Sat_SATELLITE_ALTITUDE.txt"
        self.assertIsInstance(Sat_Altitude(path), Sat_Altitude)
                
    def setUp(self):
        self.sat_altitude = Sat_Altitude("Sat_SATELLITE_ALTITUDE.txt")
        
    def test_get_orbit_number(self):
        self.assertEqual(self.sat_altitude.get_sat_altitude(0), 601674.0)
            
        
if __name__ == "__main__":
    unittest.main()
    