/*
SQLyog Community v13.1.9 (64 bit)
MySQL - 8.0.30-0ubuntu0.20.04.2 : Database - jt_temp
*********************************************************************
*/

/*!40101 SET NAMES utf8 */;

/*!40101 SET SQL_MODE=''*/;

/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;
CREATE DATABASE /*!32312 IF NOT EXISTS*/`jt_temp` /*!40100 DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci */ /*!80016 DEFAULT ENCRYPTION='N' */;

USE `jt_temp`;

/*Table structure for table `agency` */

DROP TABLE IF EXISTS `agency`;

CREATE TABLE `agency` (
  `id` int NOT NULL AUTO_INCREMENT,
  `agency_id` varchar(32) NOT NULL,
  `agency_name` varchar(32) NOT NULL,
  `agency_url` varchar(128) NOT NULL,
  `agency_timezone` varchar(32) NOT NULL,
  `agency_lang` varchar(32) NOT NULL,
  `agency_phone` varchar(32) NOT NULL,
  `agencycol` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `agency_id` (`agency_id`)
) ENGINE=InnoDB AUTO_INCREMENT=6 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

/*Data for the table `agency` */

/*Table structure for table `calendar` */

DROP TABLE IF EXISTS `calendar`;

CREATE TABLE `calendar` (
  `id` int NOT NULL AUTO_INCREMENT,
  `service_id` varchar(32) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL,
  `monday` int NOT NULL,
  `tuesday` int NOT NULL,
  `wednesday` int NOT NULL,
  `thursday` int NOT NULL,
  `friday` int NOT NULL,
  `saturday` int NOT NULL,
  `sunday` int NOT NULL,
  `start_date` datetime NOT NULL,
  `end_date` datetime NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `idx_calendar` (`service_id`,`start_date`,`end_date`)
) ENGINE=InnoDB AUTO_INCREMENT=58 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

/*Data for the table `calendar` */

/*Table structure for table `calendar_dates` */

DROP TABLE IF EXISTS `calendar_dates`;

CREATE TABLE `calendar_dates` (
  `id` int NOT NULL AUTO_INCREMENT,
  `service_id` varchar(32) NOT NULL,
  `date` datetime NOT NULL,
  `exception_type` int DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `idx_calendar_date` (`service_id`,`date`)
) ENGINE=InnoDB AUTO_INCREMENT=258 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

/*Data for the table `calendar_dates` */

/*Table structure for table `jt_user` */

DROP TABLE IF EXISTS `jt_user`;

CREATE TABLE `jt_user` (
  `id` int NOT NULL AUTO_INCREMENT COMMENT 'Primary Key',
  `username` varchar(256) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL COMMENT 'User name',
  `password_hash` varchar(60) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL COMMENT 'Bcrypt password hash',
  `nickname` varchar(256) DEFAULT NULL COMMENT 'User nickname',
  `colour` char(6) DEFAULT NULL COMMENT 'html colour code',
  `profile_picture_filename` varchar(256) DEFAULT NULL COMMENT 'Profile picture filename',
  `profile_picture` mediumblob COMMENT 'Profile picture / avatar',
  PRIMARY KEY (`id`),
  UNIQUE KEY `unique_username` (`username`)
) ENGINE=InnoDB AUTO_INCREMENT=23 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

/*Data for the table `jt_user` */

/*Table structure for table `routes` */

DROP TABLE IF EXISTS `routes`;

CREATE TABLE `routes` (
  `id` int NOT NULL AUTO_INCREMENT,
  `route_id` varchar(32) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL,
  `agency_id` varchar(32) NOT NULL,
  `route_short_name` varchar(32) NOT NULL,
  `route_long_name` varchar(128) NOT NULL,
  `route_type` int NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `route_id` (`route_id`)
) ENGINE=InnoDB AUTO_INCREMENT=464 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

/*Data for the table `routes` */

/*Table structure for table `shapes` */

DROP TABLE IF EXISTS `shapes`;

CREATE TABLE `shapes` (
  `id` int NOT NULL AUTO_INCREMENT,
  `shape_id` varchar(32) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL,
  `shape_pt_lat` double NOT NULL,
  `shape_pt_lon` double NOT NULL,
  `shape_pt_sequence` double NOT NULL,
  `shape_dist_traveled` double NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `idx_shape` (`shape_id`,`shape_pt_lat`,`shape_pt_lon`,`shape_pt_sequence`)
) ENGINE=InnoDB AUTO_INCREMENT=851913 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

/*Data for the table `shapes` */

/*Table structure for table `stop_times` */

DROP TABLE IF EXISTS `stop_times`;

CREATE TABLE `stop_times` (
  `id` int NOT NULL AUTO_INCREMENT,
  `trip_id` varchar(32) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL COMMENT 'Identifies a trip.',
  `arrival_time` time NOT NULL COMMENT 'Arrival time at a specific stop for a specific trip on a route. If there are not separate times for arrival and departure at a stop, enter the same value for arrival_time and departure_time. For times occurring after midnight on the service day, enter the time as a value greater than 24:00:00 in HH:MM:SS local time for the day on which the trip schedule begins.\n\nScheduled stops where the vehicle strictly adheres to the specified arrival and departure times are timepoints. If this stop is not a timepoint, it is recommended to provide an estimated or interpolated time. If this is not available, arrival_time can be left empty. Further, indicate that interpolated times are provided with timepoint=0. If interpolated times are indicated with timepoint=0, then time points must be indicated with timepoint=1. Provide arrival times for all stops that are time points. An arrival time must be specified for the first and the last stop in a trip.',
  `departure_time` time NOT NULL COMMENT 'Departure time from a specific stop for a specific trip on a route. For times occurring after midnight on the service day, enter the time as a value greater than 24:00:00 in HH:MM:SS local time for the day on which the trip schedule begins. If there are not separate times for arrival and departure at a stop, enter the same value for arrival_time and departure_time. See the arrival_time description for more details about using timepoints correctly.\n\nThe departure_time field should specify time values whenever possible, including non-binding estimated or interpolated times between timepoints.',
  `stop_id` varchar(16) NOT NULL COMMENT 'Identifies the serviced stop. All stops serviced during a trip must have a record in stop_times.txt. Referenced locations must be stops, not stations or station entrances. A stop may be serviced multiple times in the same trip, and multiple trips and routes may service the same stop.',
  `stop_sequence` smallint NOT NULL COMMENT 'Order of stops for a particular trip. The values must increase along the trip but do not need to be consecutive.Example: The first location on the trip could have a stop_sequence=1, the second location on the trip could have a stop_sequence=23, the third location could have a stop_sequence=40, and so on.',
  `stop_headsign` varchar(64) NOT NULL COMMENT 'Text that appears on signage identifying the trip''s destination to riders. This field overrides the default trips.trip_headsign when the headsign changes between stops. If the headsign is displayed for an entire trip, use trips.trip_headsign instead.\n\nA stop_headsign value specified for one stop_time does not apply to subsequent stop_times in the same trip. If you want to override the trip_headsign for multiple stop_times in the same trip, the stop_headsign value must be repeated in each stop_time row.',
  `pickup_type` smallint NOT NULL COMMENT 'Indicates pickup method. Valid options are:\n\n0 or empty - Regularly scheduled pickup.\n1 - No pickup available.\n2 - Must phone agency to arrange pickup.\n3 - Must coordinate with driver to arrange pickup.',
  `drop_off_type` smallint NOT NULL COMMENT 'Indicates drop off method. Valid options are:\n\n0 or empty - Regularly scheduled drop off.\n1 - No drop off available.\n2 - Must phone agency to arrange drop off.\n3 - Must coordinate with driver to arrange drop off.',
  `shape_dist_traveled` double NOT NULL COMMENT 'Actual distance traveled along the associated shape, from the first stop to the stop specified in this record. This field specifies how much of the shape to draw between any two stops during a trip. Must be in the same units used in shapes.txt. Values used for shape_dist_traveled must increase along with stop_sequence; they cannot be used to show reverse travel along a route.Example: If a bus travels a distance of 5.25 kilometers from the start of the shape to the stop, shape_dist_traveled=5.25.',
  PRIMARY KEY (`id`),
  UNIQUE KEY `idx_stop_time` (`trip_id`,`arrival_time`,`departure_time`,`stop_id`,`stop_sequence`)
) ENGINE=InnoDB AUTO_INCREMENT=3346583 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='*** Initial Post-Import Data Type Review Complete, TK, 22/06/20';

/*Data for the table `stop_times` */

/*Table structure for table `stops` */

DROP TABLE IF EXISTS `stops`;

CREATE TABLE `stops` (
  `id` int NOT NULL AUTO_INCREMENT,
  `stop_id` varchar(16) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL COMMENT 'Identifies a stop, station, or station entrance.\\n\\nThe term "station entrance" refers to both station entrances and station exits. Stops, stations or station entrances are collectively referred to as locations. Multiple routes may use the same stop.',
  `stop_name` varchar(64) NOT NULL COMMENT 'Name of the location. Use a name that people will understand in the local and tourist vernacular.\n\nWhen the location is a boarding area (location_type=4), the stop_name should contains the name of the boarding area as displayed by the agency. It could be just one letter (like on some European intercity railway stations), or text like “Wheelchair boarding area” (NYC’s Subway) or “Head of short trains” (Paris’ RER).\n\nConditionally Required:\n• Required for locations which are stops (location_type=0), stations (location_type=1) or entrances/exits (location_type=2).\n• Optional for locations which are generic nodes (location_type=3) or boarding areas (location_type=4).',
  `stop_lat` double NOT NULL COMMENT 'Latitude of the location.\n\nConditionally Required:\n• Required for locations which are stops (location_type=0), stations (location_type=1) or entrances/exits (location_type=2).\n• Optional for locations which are generic nodes (location_type=3) or boarding areas (location_type=4).',
  `stop_lon` double NOT NULL COMMENT 'Longitude of the location.\n\nConditionally Required:\n• Required for locations which are stops (location_type=0), stations (location_type=1) or entrances/exits (location_type=2).\n• Optional for locations which are generic nodes (location_type=3) or boarding areas (location_type=4).',
  `stop_position` point NOT NULL COMMENT 'Stop location as spatial point',
  `dist_from_cc` double NOT NULL COMMENT 'Distance from City Center. Our domain knowledge suggests travel times near the city center will be larger than travel times outside the city center.  So we added this column to supply an extra input to our model so we could assess it''s impact.  This column is not part of the orginal GTFS data and has been programatically populated.',
  PRIMARY KEY (`id`),
  SPATIAL KEY `stop_position` (`stop_position`),
  KEY `stop_id` (`stop_id`)
) ENGINE=InnoDB AUTO_INCREMENT=10024 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='*** Initial Post-Import Data Type Review Complete, TK, 22/06/20';

/*Data for the table `stops` */

/*Table structure for table `transfers` */

DROP TABLE IF EXISTS `transfers`;

CREATE TABLE `transfers` (
  `id` int NOT NULL AUTO_INCREMENT,
  `from_stop_id` varchar(16) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL COMMENT 'Identifies a stop or station where a connection between routes begins. If this field refers to a station, the transfer rule applies to all its child stops.',
  `to_stop_id` varchar(16) NOT NULL COMMENT 'Identifies a stop or station where a connection between routes ends. If this field refers to a station, the transfer rule applies to all child stops.',
  `transfer_type` smallint NOT NULL COMMENT 'Indicates the type of connection for the specified (from_stop_id, to_stop_id) pair. Valid options are:\\n\\n0 or empty - Recommended transfer point between routes.\\n1 - Timed transfer point between two routes. The departing vehicle is expected to wait for the arriving one and leave sufficient time for a rider to transfer between routes.\\n2 - Transfer requires a minimum amount of time between arrival and departure to ensure a connection. The time required to transfer is specified by min_transfer_time.\\n3 - Transfers are not possible between routes at the location.',
  `min_transfer_time` int DEFAULT NULL COMMENT 'Optional: Amount of time, in seconds, that must be available to permit a transfer between routes at the specified stops. The min_transfer_time should be sufficient to permit a typical rider to move between the two stops, including buffer time to allow for schedule variance on each route.',
  PRIMARY KEY (`id`),
  UNIQUE KEY `idx_transfer` (`from_stop_id`,`to_stop_id`)
) ENGINE=InnoDB AUTO_INCREMENT=7002 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='*** Initial Post-Import Data Type Review Complete, TK, 22/06/20';

/*Data for the table `transfers` */

/*Table structure for table `trips` */

DROP TABLE IF EXISTS `trips`;

CREATE TABLE `trips` (
  `id` int NOT NULL AUTO_INCREMENT,
  `route_id` varchar(32) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL,
  `service_id` varchar(32) NOT NULL,
  `trip_id` varchar(32) NOT NULL,
  `shape_id` varchar(32) NOT NULL,
  `trip_headsign` varchar(128) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL,
  `direction_id` tinyint NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `idx_trip` (`route_id`,`trip_id`,`shape_id`)
) ENGINE=InnoDB AUTO_INCREMENT=87373 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

/*Data for the table `trips` */

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;
