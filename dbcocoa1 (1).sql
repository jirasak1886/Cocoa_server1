-- phpMyAdmin SQL Dump
-- version 5.2.1
-- https://www.phpmyadmin.net/
--
-- Host: 127.0.0.1
-- Generation Time: Oct 03, 2025 at 12:43 PM
-- Server version: 10.4.32-MariaDB
-- PHP Version: 8.1.25

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
START TRANSACTION;
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- Database: `dbcocoa1`
--

-- --------------------------------------------------------

--
-- Table structure for table `fertilizer`
--

CREATE TABLE `fertilizer` (
  `id` int(11) NOT NULL,
  `code` varchar(32) DEFAULT NULL,
  `name` varchar(100) DEFAULT NULL,
  `name_th` varchar(100) DEFAULT NULL,
  `n_pct` decimal(5,2) DEFAULT 0.00,
  `p2o5_pct` decimal(5,2) DEFAULT 0.00,
  `k2o_pct` decimal(5,2) DEFAULT 0.00,
  `mg_pct` decimal(5,2) DEFAULT 0.00,
  `ca_pct` decimal(5,2) DEFAULT 0.00,
  `s_pct` decimal(5,2) DEFAULT 0.00,
  `source_form` enum('granule','liquid','powder') DEFAULT 'granule',
  `description` text DEFAULT NULL,
  `note` text DEFAULT NULL,
  `is_active` tinyint(1) DEFAULT 1,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp(),
  `updated_at` timestamp NULL DEFAULT NULL ON UPDATE current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `fertilizer`
--

INSERT INTO `fertilizer` (`id`, `code`, `name`, `name_th`, `n_pct`, `p2o5_pct`, `k2o_pct`, `mg_pct`, `ca_pct`, `s_pct`, `source_form`, `description`, `note`, `is_active`, `created_at`, `updated_at`) VALUES
(1, '15-15-15', 'Balanced', 'ปุ๋ยสมดุล', 15.00, 15.00, 15.00, 0.00, 0.00, 0.00, 'granule', 'ใช้ทั่วไป ทุกช่วงอายุ', '', 1, '2025-09-28 16:45:13', NULL),
(2, '16-16-16', 'Balanced+', 'ปุ๋ยสมดุลเข้มข้น', 16.00, 16.00, 16.00, 0.00, 0.00, 0.00, 'granule', 'ใช้ทั่วไป ต้องการธาตุเสมอสูง', '', 1, '2025-09-28 16:45:13', NULL),
(3, '20-20-20', 'Triple 20', 'สูตรเสมอเข้มข้น', 20.00, 20.00, 20.00, 0.00, 0.00, 0.00, 'liquid', 'นิยมในรูปปุ๋ยน้ำ/ฉีดพ่นทางใบ', '', 1, '2025-09-28 16:45:13', NULL),
(4, '20-10-10', 'Grow Starter', 'เร่งโต', 20.00, 10.00, 10.00, 0.00, 0.00, 0.00, 'granule', 'ช่วงตั้งตัว/เร่งใบ', '', 1, '2025-09-28 16:45:13', NULL),
(5, '25-7-7', 'Leaf Booster+', 'เร่งใบเข้มข้น+', 25.00, 7.00, 7.00, 0.00, 0.00, 0.00, 'granule', 'N สูง เร่งแตกใบ', 'ควบคุมปริมาณ', 1, '2025-09-28 16:45:13', '2025-10-02 19:38:11'),
(6, '21-0-0', 'Ammonium Sulfate', 'แอมโมเนียซัลเฟต', 21.00, 0.00, 0.00, 0.00, 0.00, 24.00, 'granule', 'n', 'ระวังกรดจัด', 1, '2025-09-28 16:45:13', NULL),
(7, '46-0-0', 'ยูเรีย', 'n', 46.00, 0.00, 0.00, 0.00, 0.00, 0.00, 'granule', 'ปุ๋ยไนโตรเจนสูง', 'เสี่ยงเผารากถ้าให้มาก', 1, '2025-09-28 16:45:13', '2025-09-30 17:48:31'),
(8, '18-46-0', 'DAP', 'DAP', 18.00, 46.00, 0.00, 0.00, 0.00, 0.00, 'granule', 'ปุ๋ยฟอสฟอรัสสูง', '', 1, '2025-09-28 16:45:13', '2025-09-29 18:58:41'),
(9, '16-20-0', 'NP Base', 'รองพื้น N-P', 16.00, 20.00, 0.00, 0.00, 0.00, 0.00, 'granule', 'ใส่รองพื้น/ก่อนออกดอก', '', 1, '2025-09-28 16:45:13', NULL),
(10, '0-20-0', 'SP', 'ซูเปอร์ฟอสเฟต', 0.00, 20.00, 0.00, 0.00, 0.00, 12.00, 'granule', 'เพิ่ม P และ S', '', 1, '2025-09-28 16:45:13', NULL),
(11, '0-46-0', 'TSP', 'ทริปเปิลซูเปอร์ฟอสเฟต', 0.00, 46.00, 0.00, 0.00, 0.00, 0.00, 'granule', 'P เข้มข้น', '', 1, '2025-09-28 16:45:13', NULL),
(12, '13-13-21', 'Fruit Set', 'บำรุงผล (P+K)', 13.00, 13.00, 21.00, 0.00, 0.00, 0.00, 'granule', 'ระยะติดผล/เพิ่มคุณภาพ', '', 1, '2025-09-28 16:45:13', NULL),
(13, '13-13-21+Mg', 'Fruit Set Mg', 'บำรุงผล + Mg', 13.00, 13.00, 21.00, 3.00, 0.00, 0.00, 'granule', 'โกโก้/ไม้ผลขาด Mg บ่อย', 'เหมาะช่วงติดผล', 1, '2025-09-28 16:45:13', NULL),
(14, '15-5-25', 'Fruit Fill', 'บำรุงผล K สูง', 15.00, 5.00, 25.00, 0.00, 0.00, 0.00, 'granule', 'ให้ผลผลิตเต็มที่', '', 1, '2025-09-28 16:45:13', NULL),
(15, '15-5-25+Mg', 'Fruit Fill Mg', 'บำรุงผล K สูง + Mg', 15.00, 5.00, 25.00, 3.00, 0.00, 0.00, 'granule', 'ช่วยคุณภาพเมล็ด/ผล', 'แนะนำโกโก้ผลดึง K/Mg มาก', 1, '2025-09-28 16:45:13', NULL),
(16, '13-7-35', 'Quality K', 'คุณภาพผลเข้ม K', 13.00, 7.00, 35.00, 0.00, 0.00, 0.00, 'granule', 'เน้นความหวาน/คุณภาพผล', '', 1, '2025-09-28 16:45:13', NULL),
(17, '8-24-24', 'PK Booster', 'PK เข้มข้น', 8.00, 24.00, 24.00, 0.00, 0.00, 0.00, 'granule', 'ช่วงติดผล-ขยายผล', '', 1, '2025-09-28 16:45:13', NULL),
(18, '0-0-50', 'K2SO4', 'โพแทสเซียมซัลเฟต', 0.00, 0.00, 50.00, 0.00, 0.00, 18.00, 'granule', 'K + S ไม่ใส่ Cl เหมาะโกโก้', '', 1, '2025-09-28 16:45:13', NULL),
(19, '0-0-60', 'MOP', 'โพแทสเซียมคลอไรด์', 0.00, 0.00, 60.00, 0.00, 0.00, 0.00, 'granule', 'ปุ๋ยโพแทสเซียมสูง', 'โกโก้ไวต่อ Cl ควรเลี่ยง', 1, '2025-09-28 16:45:13', '2025-09-29 18:58:41'),
(20, 'MgSO4', 'Epsom Salt', 'แมกนีเซียมซัลเฟต', 0.00, 0.00, 0.00, 9.80, 0.00, 13.00, 'powder', 'แก้ขาด Mg ใบเหลืองระหว่างเส้นใบ', 'พ่นทางใบได้', 1, '2025-09-28 16:45:13', NULL),
(21, 'Dolomite', 'Dolomite', 'โดโลไมต์', 0.00, 0.00, 0.00, 10.00, 20.00, 0.00, 'granule', 'ปรับดิน + เพิ่ม Ca/Mg', 'ค่อย ๆ ปรับ pH', 1, '2025-09-28 16:45:13', NULL),
(22, 'Gypsum', 'Gypsum', 'ยิปซัม', 0.00, 0.00, 0.00, 0.00, 23.00, 18.00, 'granule', 'เพิ่ม Ca + S ปรับโครงสร้างดิน', '', 1, '2025-09-28 16:45:13', NULL),
(23, '10-5-20(OC)', 'Organic-Compound', 'อินทรีย์เคมี 10-5-20', 10.00, 5.00, 20.00, 0.00, 0.00, 0.00, 'granule', 'ครึ่งอินทรีย์ครึ่งเคมี', 'เพิ่มอินทรียวัตถุ', 1, '2025-09-28 16:45:13', NULL),
(24, 'Org-Base', 'Organic', 'ปุ๋ยอินทรีย์พื้นฐาน', 1.00, 1.00, 1.00, 0.00, 2.00, 0.00, 'granule', 'เน้นปรับดิน/โครงสร้าง', 'ตัวเลขเป็นค่าเฉลี่ย', 1, '2025-09-28 16:45:13', NULL),
(36, '12-61-0', 'MAP', 'โมโนแอมโมเนียมฟอสเฟต', 12.00, 61.00, 0.00, 0.00, 0.00, 0.00, 'granule', 'P เข้มข้น ใช้รองพื้น/พ่นใบ', NULL, 1, '2025-10-02 19:38:11', NULL),
(37, '13-0-46', 'KNO3', 'โพแทสเซียมไนเตรต', 13.00, 0.00, 46.00, 0.00, 0.00, 0.00, 'granule', 'เพิ่ม K แบบไม่มี Cl เหมาะโกโก้', NULL, 1, '2025-10-02 19:38:11', '2025-10-02 19:46:24'),
(38, '0-52-34', 'MKP', 'โมโนโพแทสเซียมฟอสเฟต', 0.00, 52.00, 34.00, 0.00, 0.00, 0.00, 'powder', 'เสริม P+K ไม่มี Cl ใช้พ่นได้', NULL, 1, '2025-10-02 19:38:11', '2025-10-02 19:46:24'),
(39, '0-0-52', 'SOP (powder)', 'โพแทสเซียมซัลเฟต (ผง)', 0.00, 0.00, 52.00, 0.00, 0.00, 18.00, 'powder', 'SOP เกรดผง สำหรับละลายน้ำ/พ่น', NULL, 1, '2025-10-02 19:38:11', '2025-10-02 19:46:24'),
(40, '12-12-17+2Mg', 'Fruit Base Mg', 'สูตรเสมอเอนเอียง K + Mg', 12.00, 12.00, 17.00, 2.00, 0.00, 0.00, 'granule', 'เหมาะไม้ผล/โกโก้', NULL, 1, '2025-10-02 19:38:11', NULL),
(41, '20-10-10+Mg', 'Grow Starter Mg', 'เร่งโต + เสริม Mg', 20.00, 10.00, 10.00, 2.00, 0.00, 0.00, 'granule', 'ช่วงตั้งตัวมีขาด Mg ร่วม', NULL, 1, '2025-10-02 19:38:11', '2025-10-02 19:46:24'),
(42, '14-7-35+Mg', 'Quality K Mg', 'K สูงคุณภาพผล + Mg', 14.00, 7.00, 35.00, 2.00, 0.00, 0.00, 'granule', 'ระยะขยายผล', NULL, 1, '2025-10-02 19:38:11', '2025-10-02 19:46:24'),
(43, '13-7-35+2Mg', 'Quality K 2Mg', 'K สูงมาก + Mg เข้ม', 13.00, 7.00, 35.00, 2.00, 0.00, 0.00, 'granule', 'ระยะท้าย', NULL, 1, '2025-10-02 19:38:11', '2025-10-02 19:46:24'),
(44, 'Kieserite', 'Kieserite', 'ไคเซอไรต์ (MgSO4·H2O)', 0.00, 0.00, 0.00, 15.00, 0.00, 20.00, 'granule', 'Mg แบบเม็ด ปลดปล่อยช้า', NULL, 1, '2025-10-02 19:38:11', '2025-10-02 19:46:24'),
(45, 'CaNO3', 'Calcium Nitrate', 'ปุ๋ยแคลเซียมไนเตรต (15.5-0-0)', 15.50, 0.00, 0.00, 0.00, 19.00, 0.00, 'granule', 'เสริม N พร้อม Ca', NULL, 1, '2025-10-02 19:38:11', '2025-10-02 19:46:24');

-- --------------------------------------------------------

--
-- Table structure for table `field`
--

CREATE TABLE `field` (
  `field_id` int(11) NOT NULL,
  `field_name` varchar(100) NOT NULL,
  `size_square_meter` decimal(12,2) DEFAULT NULL,
  `user_id` int(11) DEFAULT NULL,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `field`
--

INSERT INTO `field` (`field_id`, `field_name`, `size_square_meter`, `user_id`, `created_at`) VALUES
(1, 'Test Field', NULL, 1, '2025-09-29 18:31:14'),
(4, 'a', 1200.00, 4, '2025-09-09 10:07:32'),
(7, 's', 1600.00, 4, '2025-09-09 16:38:51'),
(8, 'a', 166.00, 5, '2025-09-11 02:38:53'),
(9, 'B', 1666.00, 5, '2025-09-12 18:59:07'),
(10, 'ทดสอบนะ', 600.00, 5, '2025-09-14 08:38:12'),
(11, 'a', 1600.00, 7, '2025-09-16 18:28:47'),
(12, 'b', 1600.00, 7, '2025-09-21 18:00:30'),
(13, 'แปลง0', 201.00, 9, '2025-09-22 09:00:25'),
(15, 'Demo Farm', 8000.00, 11, '2025-09-29 18:38:09');

-- --------------------------------------------------------

--
-- Table structure for table `field_point`
--

CREATE TABLE `field_point` (
  `point_id` int(11) NOT NULL,
  `field_id` int(11) NOT NULL,
  `latitude` double NOT NULL,
  `longitude` double NOT NULL,
  `point_order` int(11) NOT NULL,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `field_point`
--

INSERT INTO `field_point` (`point_id`, `field_id`, `latitude`, `longitude`, `point_order`, `created_at`) VALUES
(17, 7, 7.8300672, 99.9332475, 1, '2025-09-09 16:38:51'),
(18, 7, 7.8300672, 99.9332475, 2, '2025-09-09 16:38:51'),
(22, 4, 7.6201, 100.0751, 1, '2025-09-10 17:39:32'),
(23, 4, 7.6205, 100.0759, 2, '2025-09-10 17:39:32'),
(24, 4, 7.8096973, 99.9353428, 3, '2025-09-10 17:39:32'),
(25, 4, 7.8273331, 99.9353427, 4, '2025-09-10 17:39:32'),
(32, 10, 7.8082956, 99.941491, 1, '2025-09-14 08:38:43'),
(33, 10, 7.8082118, 99.9414394, 2, '2025-09-14 08:38:43'),
(34, 9, 7.8322896, 99.9392111, 1, '2025-09-14 17:42:47'),
(35, 9, 7.8322896, 99.9392111, 2, '2025-09-14 17:42:47'),
(36, 9, 7.8597447, 99.8348255, 3, '2025-09-14 17:42:47'),
(78, 11, 7.831441304881643, 99.93313828400446, 1, '2025-09-21 17:57:47'),
(79, 11, 7.827915940730975, 99.93355250629882, 2, '2025-09-21 17:57:47'),
(80, 11, 7.827822676731667, 99.9383348798698, 3, '2025-09-21 17:57:47'),
(81, 11, 7.8320381883632635, 99.93816542679664, 4, '2025-09-21 17:57:47'),
(82, 11, 7.8316091781804715, 99.93311945604484, 5, '2025-09-21 17:57:47'),
(83, 11, 7.831440241939709, 99.93313828400446, 6, '2025-09-21 17:57:47'),
(85, 12, 7.8273331, 99.9353427, 1, '2025-09-21 18:01:37'),
(86, 12, 7.829733052012485, 99.93351640911312, 2, '2025-09-21 18:01:37'),
(87, 12, 7.831080910600418, 99.93827070737008, 3, '2025-09-21 18:01:37'),
(88, 12, 7.82783533515937, 99.93851547515479, 4, '2025-09-21 18:01:37'),
(89, 12, 7.827275750742335, 99.9353146731767, 5, '2025-09-21 18:01:37'),
(92, 13, 7.809537676623365, 99.9363617608482, 1, '2025-09-22 09:09:20'),
(93, 13, 7.809446937292933, 99.93596400376896, 2, '2025-09-22 09:09:20'),
(94, 13, 7.809750265854425, 99.93588026548117, 3, '2025-09-22 09:09:20'),
(95, 13, 7.809853967869457, 99.93629372340511, 4, '2025-09-22 09:09:20'),
(96, 13, 7.809535084110904, 99.93635391030107, 5, '2025-09-22 09:09:20');

-- --------------------------------------------------------

--
-- Table structure for table `mark_zone`
--

CREATE TABLE `mark_zone` (
  `mark_id` int(11) NOT NULL,
  `zone_id` int(11) NOT NULL,
  `tree_no` int(11) DEFAULT NULL,
  `latitude` double DEFAULT NULL,
  `longitude` double DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `mark_zone`
--

INSERT INTO `mark_zone` (`mark_id`, `zone_id`, `tree_no`, `latitude`, `longitude`) VALUES
(15, 4, 1, 7.8300672, 99.9332475),
(16, 4, 2, 7.8300672, 99.9332475),
(17, 3, 1, 7.8300672, 99.9332475),
(18, 3, 2, 7.8300672, 99.9332475),
(19, 5, 1, 7.8082526, 99.9415216),
(20, 5, 2, 7.8082526, 99.9415216),
(21, 2, 1, 7.8300672, 99.9332475),
(22, 2, 2, 7.6834324333333335, 100.02878093333334),
(23, 2, 3, 7.8300672, 99.9332475),
(24, 2, 4, 7.8273331, 99.9353427),
(25, 6, 1, 7.8123737, 99.9374381),
(26, 6, 2, 7.8123737, 99.9374381),
(29, 8, 1, 7.8082048, 99.9414213),
(30, 8, 2, 7.8082662, 99.9414554),
(31, 8, 3, 7.8082538, 99.9414454),
(32, 8, 4, 7.8082537, 99.9414652),
(33, 8, 5, 7.8082232, 99.9414267),
(34, 7, 1, 7.8322896, 99.9392111),
(35, 7, 2, 7.8322896, 99.9392111),
(36, 7, 3, 7.8597447, 99.8348255),
(94, 10, 1, 7.830590009729114, 99.9343899518966),
(95, 10, 2, 7.831610372697844, 99.9343212874113),
(96, 10, 3, 7.831703905700324, 99.9354671272989),
(97, 10, 4, 7.830560249239496, 99.93560445626952),
(98, 10, 5, 7.830547494557942, 99.9343899518966),
(99, 11, 1, 7.830339350658407, 99.93566076719164),
(100, 11, 2, 7.829072396047036, 99.93619720899461),
(101, 11, 3, 7.828362389663439, 99.93458359211675),
(102, 11, 4, 7.82973563466875, 99.93349783377654),
(103, 11, 5, 7.830347853810764, 99.93565218425375),
(104, 9, 1, 7.830511815035986, 99.93324393978223),
(105, 9, 2, 7.830567773290409, 99.93435480663837),
(106, 9, 3, 7.83157501595953, 99.93427949336335),
(107, 9, 4, 7.831556363965532, 99.93320628386297),
(108, 9, 5, 7.830605078433392, 99.93324393978223),
(109, 9, 6, 7.830511859433183, 99.93324566336392),
(110, 12, 1, 7.831776134567229, 99.93555769943266),
(111, 12, 2, 7.830619723706454, 99.93568215399644),
(112, 12, 3, 7.830811041828311, 99.93697390579253),
(113, 12, 4, 7.831846023178578, 99.93683487298718),
(114, 12, 5, 7.831748066482244, 99.935558434294),
(118, 15, 1, 7.830381924503281, 99.93571835077557),
(119, 15, 2, 7.8290906712034705, 99.93621274561907),
(120, 15, 3, 7.829651698922937, 99.93833414881031),
(121, 15, 4, 7.831072817562508, 99.93822284583224),
(122, 15, 5, 7.830438626653708, 99.93568103249675);

--
-- Triggers `mark_zone`
--
DELIMITER $$
CREATE TRIGGER `mark_zone_ad` AFTER DELETE ON `mark_zone` FOR EACH ROW BEGIN
  UPDATE zone z
  SET z.mark_count = (SELECT COUNT(*) FROM mark_zone m WHERE m.zone_id = OLD.zone_id)
  WHERE z.zone_id = OLD.zone_id;
END
$$
DELIMITER ;
DELIMITER $$
CREATE TRIGGER `mark_zone_ai` AFTER INSERT ON `mark_zone` FOR EACH ROW BEGIN
  UPDATE zone z
  SET z.mark_count = (SELECT COUNT(*) FROM mark_zone m WHERE m.zone_id = NEW.zone_id)
  WHERE z.zone_id = NEW.zone_id;
END
$$
DELIMITER ;
DELIMITER $$
CREATE TRIGGER `mark_zone_au` AFTER UPDATE ON `mark_zone` FOR EACH ROW BEGIN
  IF OLD.zone_id <> NEW.zone_id THEN
    UPDATE zone z
    SET z.mark_count = (SELECT COUNT(*) FROM mark_zone m WHERE m.zone_id = OLD.zone_id)
    WHERE z.zone_id = OLD.zone_id;

    UPDATE zone z
    SET z.mark_count = (SELECT COUNT(*) FROM mark_zone m WHERE m.zone_id = NEW.zone_id)
    WHERE z.zone_id = NEW.zone_id;
  END IF;
END
$$
DELIMITER ;

-- --------------------------------------------------------

--
-- Table structure for table `nutrient_deficiency`
--

CREATE TABLE `nutrient_deficiency` (
  `nutrient_code` varchar(20) NOT NULL,
  `nutrient_name` varchar(100) NOT NULL,
  `common_symptoms` text DEFAULT NULL,
  `diagnostic_notes` text DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `nutrient_deficiency`
--

INSERT INTO `nutrient_deficiency` (`nutrient_code`, `nutrient_name`, `common_symptoms`, `diagnostic_notes`) VALUES
('ALL', 'All nutrients / Balanced', NULL, NULL),
('K', 'Potassium deficiency', 'ขอบใบไหม้ จุดซีดกระจาย', 'ดูใบล่างชัดเจน'),
('Mg', 'Magnesium deficiency', 'เหลืองระหว่างเส้นใบ ใบแก่ก่อน', 'ดูแพทเทิร์นสลับเส้นใบ'),
('N', 'Nitrogen deficiency', 'ใบเหลืองซีดจากโคนไปปลาย', 'ดูใบแก่ก่อน'),
('P', 'Phosphorus deficiency', 'ใบม่วง/เขียวเข้ม การเจริญเติบโตช้า', 'ดูใบแก่ช่วงฐานกิ่ง');

-- --------------------------------------------------------

--
-- Table structure for table `password_reset_tokens`
--

CREATE TABLE `password_reset_tokens` (
  `id` int(11) NOT NULL,
  `user_id` int(11) NOT NULL,
  `token_hash` char(64) NOT NULL,
  `channel` enum('email','sms') NOT NULL DEFAULT 'email',
  `destination` varchar(255) NOT NULL,
  `expires_at` datetime NOT NULL,
  `used_at` datetime DEFAULT NULL,
  `attempts` int(11) NOT NULL DEFAULT 0,
  `created_at` datetime NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `password_reset_tokens`
--

INSERT INTO `password_reset_tokens` (`id`, `user_id`, `token_hash`, `channel`, `destination`, `expires_at`, `used_at`, `attempts`, `created_at`) VALUES
(1, 7, 'e3f4e31578204a31666097622b7e46d857de12af51f264e3e5ab8472a9f2217e', 'email', '652021044@tsu.ac.th', '2025-09-18 20:28:46', '2025-09-18 20:19:18', 0, '2025-09-19 03:18:46'),
(2, 7, 'f5bcd0adfeeb47a7fa1d0ccdb7287f993f488bdd675be33eda4a7b15df553d90', 'email', '652021044@tsu.ac.th', '2025-09-18 20:37:19', '2025-09-18 20:27:38', 0, '2025-09-19 03:27:19'),
(3, 7, 'd3db87a2be07022de3326aa6bb0d2bd2d7a7b1455158495961f62dc6ca236bfb', 'email', '652021044@tsu.ac.th', '2025-09-18 21:16:01', '2025-09-18 21:06:30', 0, '2025-09-19 04:06:01'),
(4, 7, 'ff92c9932529086c081aa7a1fdb1d338712c2981bacb43aea113270b8994a28f', 'email', '652021044@tsu.ac.th', '2025-09-19 17:33:43', '2025-09-19 17:54:44', 0, '2025-09-20 00:23:43'),
(5, 7, '747c123c36abf3a0e595bd5f93947cb2d5c5d3a3c3a0eb06c424fb534b926eac', 'email', '652021044@tsu.ac.th', '2025-09-19 17:36:25', '2025-09-19 17:54:44', 0, '2025-09-20 00:26:25'),
(6, 7, '120257ebfc4d2864545f360ecf1132f1817a8096becb907fdaac9c9da08c1c47', 'email', '652021044@tsu.ac.th', '2025-09-19 17:40:17', '2025-09-19 17:54:44', 0, '2025-09-20 00:30:17'),
(7, 7, '676ddbd35e43b1a47f64c2207d2f77f95070039cf9a9258cc937b39d64a2c6aa', 'email', '652021044@tsu.ac.th', '2025-09-19 17:43:17', '2025-09-19 17:54:44', 0, '2025-09-20 00:33:17'),
(8, 7, 'de9e85cf7d41feb364d50d09888bf1a8202a54a81cfb315b5f3eaf479de2aa13', 'email', '652021044@tsu.ac.th', '2025-09-19 17:49:35', '2025-09-19 17:54:44', 0, '2025-09-20 00:39:35'),
(9, 7, '8230a13d34ea29b29c952256b45d580f8f34f9e5a81efab7b209a5aba1a6baa3', 'email', '652021044@tsu.ac.th', '2025-09-19 17:55:12', '2025-09-19 17:54:44', 0, '2025-09-20 00:45:12'),
(10, 7, '699787b94cf18d6b96e4bb69a8c16323728ce2723a4eeb9baff0165bf6a09dbc', 'email', '652021044@tsu.ac.th', '2025-09-19 18:03:53', '2025-09-19 17:54:24', 0, '2025-09-20 00:53:53'),
(11, 7, '2e744b0f16a59d7c9a05d9d7d3296362d8cf0ade479e423f4e821af6913f435a', 'email', '652021044@tsu.ac.th', '2025-09-19 18:10:31', '2025-09-19 18:00:47', 0, '2025-09-20 01:00:31'),
(12, 7, '451015fe929680b966d9aa3f696916b0074b58d8e684402a430f08bf17477a03', 'email', '652021044@tsu.ac.th', '2025-09-20 07:59:15', NULL, 0, '2025-09-20 14:49:15'),
(13, 9, 'f520798fc3476fe6df7e10c58348fc89b378fb025b8dc97b2b8f1c0e8f223ed8', 'email', '652021054@tsu.ac.th', '2025-09-22 09:47:06', '2025-09-22 09:38:10', 0, '2025-09-22 16:37:06'),
(14, 9, '8f72291abc2ce364e4625b2574f1e6655ee1d7f15fc7190acc2780c4e0924d6a', 'email', '652021054@tsu.ac.th', '2025-09-22 09:47:32', '2025-09-22 09:40:39', 0, '2025-09-22 16:37:32'),
(15, 9, '1dbca181841de397f3b2a56d8260bd877d6b7741995b4f99ad049fbd22d90f82', 'email', '652021054@tsu.ac.th', '2025-09-22 09:48:47', '2025-09-22 09:39:41', 0, '2025-09-22 16:38:47');

-- --------------------------------------------------------

--
-- Table structure for table `users`
--

CREATE TABLE `users` (
  `user_id` int(11) NOT NULL,
  `username` varchar(50) DEFAULT NULL,
  `user_email` varchar(255) DEFAULT NULL,
  `user_tel` varchar(50) DEFAULT NULL,
  `user_password` varchar(255) DEFAULT NULL,
  `name` varchar(50) DEFAULT NULL,
  `password_changed_at` datetime DEFAULT NULL COMMENT 'เวลาที่ผู้ใช้เปลี่ยนรหัสผ่านล่าสุด',
  `created_at` timestamp NULL DEFAULT current_timestamp() COMMENT 'เวลาสร้างแถว',
  `updated_at` timestamp NULL DEFAULT current_timestamp() ON UPDATE current_timestamp() COMMENT 'เวลาอัปเดตแถวล่าสุด'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `users`
--

INSERT INTO `users` (`user_id`, `username`, `user_email`, `user_tel`, `user_password`, `name`, `password_changed_at`, `created_at`, `updated_at`) VALUES
(4, 'k12', NULL, '03289855666', '$2b$12$gXIabKGle60aXol72X7IAONlSYr5f.lm6rruweVxDYzWhM/XRPSlC', 'kkkkk', '2025-09-17 00:55:15', '2025-09-16 17:55:15', '2025-09-16 17:55:15'),
(5, 'k13', NULL, '03555555555', '$2b$12$.GabPQkCPJ/u0J.7KT3YUu9OiT2syV2Ee5fWekLkHmycucGdiGYPm', 'kkkkkkk0', '2025-09-17 00:55:15', '2025-09-16 17:55:15', '2025-09-16 17:55:15'),
(6, 'k14', NULL, '087549481619164', '$2b$12$riG74YFC0d9SGHWU11Bxy...EKyggWq9mDyxYJdGLsmwYCj.VlE1m', 'k14', '2025-09-17 00:55:15', '2025-09-16 17:55:15', '2025-09-16 17:55:15'),
(7, 'k15', '652021044@tsu.ac.th', '0235555555', '$2b$12$0IhY/6ABdZ/pwf./w33VBewjZw2r5RfmCs7K.l.MVqQpaR/J7Cmqm', 'kkkkkk', '2025-09-19 17:55:14', '2025-09-16 18:07:06', '2025-09-19 17:55:14'),
(8, 'k16', 'jirasak1776@gmail.com', '0955555555', '$2b$12$Kynrq58rXCmsvq3/Y9oap.HIWJjIZPLqF8SATCpydQC/y/Qj42qM.', 'kkkk kkk', NULL, '2025-09-22 07:26:24', '2025-09-22 07:27:14'),
(9, 'tai11', '652021054@tsu.ac.th', '0936451789', '$2b$12$S4.aof75IirO20lB7XqkJ.ShvOU7JI6KM4z7koFpktbub82qCT8yC', 'tai tai', '2025-09-22 16:40:39', '2025-09-22 08:55:17', '2025-09-22 09:40:39'),
(10, 'tai1', '652021054@tsu.ac.thf', '0215467857', '$2b$12$ZUgBuXFPaQF83oatN9WhyOYCjr9qPnAiot8bhHVBGtyP.g5PTOzSy', 'tai tai1', NULL, '2025-09-22 08:57:27', '2025-09-22 08:57:27'),
(11, 'testuser', 'test@example.com', '0000000000', '123456', 'Test User', NULL, '2025-09-29 18:33:19', '2025-09-29 18:33:19');

-- --------------------------------------------------------

--
-- Table structure for table `zone`
--

CREATE TABLE `zone` (
  `zone_id` int(11) NOT NULL,
  `zone_name` varchar(50) NOT NULL,
  `num_trees` int(11) DEFAULT 0,
  `field_id` int(11) NOT NULL,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp(),
  `mark_count` int(11) NOT NULL DEFAULT 0
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `zone`
--

INSERT INTO `zone` (`zone_id`, `zone_name`, `num_trees`, `field_id`, `created_at`, `mark_count`) VALUES
(2, 'a1', 4, 4, '2025-09-09 10:22:20', 4),
(3, 'k1', 2, 4, '2025-09-09 14:52:18', 2),
(4, 'a2', 2, 4, '2025-09-09 15:20:28', 2),
(5, '2', 2, 7, '2025-09-10 02:11:13', 2),
(6, 'a1', 2, 8, '2025-09-11 02:39:04', 2),
(7, 'b1', 3, 9, '2025-09-12 18:59:25', 3),
(8, 'โซนมืด', 5, 10, '2025-09-14 08:41:15', 5),
(9, 'a1', 20, 11, '2025-09-16 18:29:16', 6),
(10, 'a2', 20, 11, '2025-09-21 14:00:59', 5),
(11, 'b1', 20, 12, '2025-09-21 18:00:44', 5),
(12, 'a3', 20, 11, '2025-09-22 08:30:31', 5),
(13, 'โซน3', 25, 13, '2025-09-22 09:10:28', 0),
(15, 'b2', 20, 12, '2025-09-22 10:05:54', 5),
(16, 'Zone A', 0, 1, '2025-09-29 18:38:22', 0);

-- --------------------------------------------------------

--
-- Table structure for table `zone_inspection`
--

CREATE TABLE `zone_inspection` (
  `inspection_id` int(11) NOT NULL,
  `field_id` int(11) NOT NULL,
  `zone_id` int(11) NOT NULL,
  `round_no` int(11) NOT NULL,
  `inspected_at` datetime DEFAULT current_timestamp(),
  `inspector_user_id` int(11) DEFAULT NULL,
  `method` enum('manual','drone','satellite') DEFAULT 'manual',
  `status` enum('pending','completed','cancelled') DEFAULT 'pending',
  `notes` text DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Table structure for table `zone_inspection_finding`
--

CREATE TABLE `zone_inspection_finding` (
  `finding_id` int(11) NOT NULL,
  `inspection_id` int(11) NOT NULL,
  `nutrient_code` varchar(20) NOT NULL,
  `severity` enum('none','mild','moderate','severe') DEFAULT 'mild',
  `confidence` decimal(5,2) DEFAULT NULL,
  `area_percent` decimal(5,2) DEFAULT NULL,
  `trees_affected` int(11) DEFAULT NULL,
  `notes` text DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Table structure for table `zone_inspection_image`
--

CREATE TABLE `zone_inspection_image` (
  `image_id` int(11) NOT NULL,
  `inspection_id` int(11) NOT NULL,
  `image_path` varchar(255) NOT NULL,
  `captured_at` datetime DEFAULT NULL,
  `meta` longtext CHARACTER SET utf8mb4 COLLATE utf8mb4_bin DEFAULT NULL CHECK (json_valid(`meta`)),
  `file_name` varchar(255) DEFAULT NULL,
  `file_path` varchar(500) DEFAULT NULL,
  `created_at` datetime DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Triggers `zone_inspection_image`
--
DELIMITER $$
CREATE TRIGGER `trg_limit_images_per_inspection` BEFORE INSERT ON `zone_inspection_image` FOR EACH ROW BEGIN
  DECLARE img_count INT;
  SELECT COUNT(*) INTO img_count
  FROM zone_inspection_image
  WHERE inspection_id = NEW.inspection_id;
  IF img_count >= 5 THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'ไม่สามารถเพิ่มรูปได้เกิน 5 รูปต่อรอบการตรวจ';
  END IF;
END
$$
DELIMITER ;

-- --------------------------------------------------------

--
-- Table structure for table `zone_inspection_recommendation`
--

CREATE TABLE `zone_inspection_recommendation` (
  `recommendation_id` int(11) NOT NULL,
  `inspection_id` int(11) NOT NULL,
  `fertilizer_id` int(11) DEFAULT NULL,
  `nutrient_code` varchar(20) DEFAULT NULL,
  `recommendation_text` text DEFAULT NULL,
  `rate_per_area` varchar(60) DEFAULT NULL,
  `application_method` enum('soil','foliar','fertigation','other') DEFAULT 'soil',
  `status` enum('suggested','applied','skipped') DEFAULT 'suggested',
  `applied_date` date DEFAULT NULL,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `zone_inspection_recommendation`
--

INSERT INTO `zone_inspection_recommendation` (`recommendation_id`, `inspection_id`, `fertilizer_id`, `nutrient_code`, `recommendation_text`, `rate_per_area`, `application_method`, `status`, `applied_date`, `created_at`) VALUES
(3, 22, NULL, 'Mg', 'ปรับแมกนีเซียม/ปรับสภาพดิน', '50-100 กก./ไร่', 'soil', 'suggested', NULL, '2025-09-09 16:58:56'),
(4, 23, NULL, 'Mg', 'ปรับแมกนีเซียม/ปรับสภาพดิน', '50-100 กก./ไร่', 'soil', 'suggested', NULL, '2025-09-09 18:23:34'),
(5, 67, 4, 'Mg', 'ปรับ Mg และค่า pH บางส่วน', '10–25 กก./ไร่', '', 'applied', '2025-09-13', '2025-09-12 16:09:47'),
(6, 67, 3, 'K', 'เพิ่มโพแทสเซียม/คุณภาพผล', '10–20 กก./ไร่', '', 'applied', '2025-09-13', '2025-09-12 18:10:27'),
(7, 68, 4, 'Mg', 'ปรับ Mg และค่า pH บางส่วน', '10–25 กก./ไร่', '', 'applied', '2025-09-13', '2025-09-12 18:59:48'),
(8, 69, 1, 'N', 'เพิ่มไนโตรเจนอย่างรวดเร็ว', '5–10 กก./ไร่', '', 'suggested', NULL, '2025-09-14 08:52:33'),
(9, 70, 4, 'Mg', 'ปรับ Mg และค่า pH บางส่วน', NULL, NULL, 'suggested', NULL, '2025-09-16 18:30:00'),
(10, 70, 3, 'K', 'เพิ่มโพแทสเซียม/คุณภาพผล', NULL, NULL, 'suggested', NULL, '2025-09-16 18:30:00'),
(11, 70, 1, 'N', 'เพิ่มไนโตรเจนอย่างรวดเร็ว', NULL, NULL, 'suggested', NULL, '2025-09-18 14:32:14'),
(12, 71, 1, 'N', 'เพิ่มไนโตรเจนอย่างรวดเร็ว', NULL, NULL, 'suggested', NULL, '2025-09-18 14:42:08'),
(13, 73, 1, 'N', 'เพิ่มไนโตรเจนอย่างรวดเร็ว', NULL, NULL, 'suggested', NULL, '2025-09-22 09:25:20'),
(14, 73, 2, 'P', 'บูสต์ฟอสฟอรัส/ราก', NULL, NULL, 'suggested', NULL, '2025-09-22 09:25:20'),
(15, 73, 3, 'K', 'เพิ่มโพแทสเซียม/คุณภาพผล', NULL, NULL, 'suggested', NULL, '2025-09-22 09:25:20'),
(16, 74, 1, 'N', 'เพิ่มไนโตรเจนอย่างรวดเร็ว', NULL, NULL, 'suggested', NULL, '2025-09-22 09:27:30'),
(17, 74, 3, 'K', 'เพิ่มโพแทสเซียม/คุณภาพผล', NULL, NULL, 'suggested', NULL, '2025-09-22 09:27:30'),
(18, 74, 2, 'P', 'บูสต์ฟอสฟอรัส/ราก', NULL, NULL, 'suggested', NULL, '2025-09-22 09:27:30'),
(19, 72, 1, 'N', 'เพิ่มไนโตรเจนอย่างรวดเร็ว', NULL, NULL, 'suggested', NULL, '2025-09-23 11:02:10'),
(20, 75, 1, 'N', 'เพิ่มไนโตรเจนอย่างรวดเร็ว', NULL, NULL, 'suggested', NULL, '2025-09-23 11:04:45'),
(21, 76, 3, 'K', 'เพิ่มโพแทสเซียม/คุณภาพผล', NULL, NULL, 'suggested', NULL, '2025-09-23 11:06:33'),
(22, 76, 1, 'N', 'เพิ่มไนโตรเจนอย่างรวดเร็ว', NULL, NULL, 'suggested', NULL, '2025-09-23 11:06:33'),
(23, 77, 1, 'N', 'เพิ่มไนโตรเจนอย่างรวดเร็ว', NULL, NULL, 'suggested', NULL, '2025-09-23 11:11:04'),
(24, 78, 1, 'N', 'เพิ่มไนโตรเจนอย่างรวดเร็ว', NULL, NULL, 'suggested', NULL, '2025-09-23 11:13:07'),
(25, 79, 3, 'K', 'เพิ่มโพแทสเซียม/คุณภาพผล', NULL, NULL, 'suggested', NULL, '2025-09-23 11:15:21'),
(26, 79, 2, 'P', 'บูสต์ฟอสฟอรัส/ราก', NULL, NULL, 'suggested', NULL, '2025-09-23 11:15:21'),
(27, 80, 3, 'K', 'เพิ่มโพแทสเซียม/คุณภาพผล', NULL, NULL, 'suggested', NULL, '2025-09-23 11:16:06'),
(28, 81, 1, 'N', 'เพิ่มไนโตรเจนอย่างรวดเร็ว', NULL, NULL, 'suggested', NULL, '2025-09-23 11:17:17'),
(29, 81, 3, 'K', 'เพิ่มโพแทสเซียม/คุณภาพผล', NULL, NULL, 'suggested', NULL, '2025-09-23 11:17:17'),
(30, 82, 2, 'P', 'บูสต์ฟอสฟอรัส/ราก', NULL, NULL, 'suggested', NULL, '2025-09-23 11:20:09'),
(31, 83, 3, 'K', 'เพิ่มโพแทสเซียม/คุณภาพผล', NULL, NULL, 'suggested', NULL, '2025-09-23 11:22:43'),
(32, 83, 4, 'Mg', 'ปรับ Mg และค่า pH บางส่วน', NULL, NULL, 'suggested', NULL, '2025-09-23 11:22:43'),
(33, 84, 4, 'Mg', 'ปรับ Mg และค่า pH บางส่วน', NULL, NULL, 'suggested', NULL, '2025-09-23 11:24:30'),
(34, 84, 2, 'P', 'บูสต์ฟอสฟอรัส/ราก', NULL, NULL, 'suggested', NULL, '2025-09-23 11:24:30'),
(35, 85, 1, 'N', 'เพิ่มไนโตรเจนอย่างรวดเร็ว', NULL, NULL, 'suggested', NULL, '2025-09-23 16:11:39');

--
-- Indexes for dumped tables
--

--
-- Indexes for table `fertilizer`
--
ALTER TABLE `fertilizer`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `code` (`code`),
  ADD KEY `idx_fertilizer_active` (`is_active`),
  ADD KEY `idx_fertilizer_name_th` (`name_th`);

--
-- Indexes for table `field`
--
ALTER TABLE `field`
  ADD PRIMARY KEY (`field_id`),
  ADD KEY `user_id` (`user_id`);

--
-- Indexes for table `field_point`
--
ALTER TABLE `field_point`
  ADD PRIMARY KEY (`point_id`),
  ADD KEY `field_id` (`field_id`);

--
-- Indexes for table `mark_zone`
--
ALTER TABLE `mark_zone`
  ADD PRIMARY KEY (`mark_id`),
  ADD UNIQUE KEY `uq_mark_zone` (`zone_id`,`tree_no`),
  ADD KEY `idx_mark_zone_zone_id` (`zone_id`);

--
-- Indexes for table `nutrient_deficiency`
--
ALTER TABLE `nutrient_deficiency`
  ADD PRIMARY KEY (`nutrient_code`);

--
-- Indexes for table `password_reset_tokens`
--
ALTER TABLE `password_reset_tokens`
  ADD PRIMARY KEY (`id`),
  ADD KEY `idx_user_id` (`user_id`),
  ADD KEY `idx_token_hash` (`token_hash`);

--
-- Indexes for table `users`
--
ALTER TABLE `users`
  ADD PRIMARY KEY (`user_id`),
  ADD UNIQUE KEY `uq_user_email` (`user_email`);

--
-- Indexes for table `zone`
--
ALTER TABLE `zone`
  ADD PRIMARY KEY (`zone_id`),
  ADD UNIQUE KEY `uq_zone_field` (`zone_id`,`field_id`),
  ADD KEY `field_id` (`field_id`);

--
-- Indexes for table `zone_inspection`
--
ALTER TABLE `zone_inspection`
  ADD PRIMARY KEY (`inspection_id`),
  ADD UNIQUE KEY `uniq_field_zone_round` (`field_id`,`zone_id`,`round_no`),
  ADD KEY `idx_zone_time` (`zone_id`,`inspected_at`),
  ADD KEY `fk_inspection_zone_in_field` (`zone_id`,`field_id`);

--
-- Indexes for table `zone_inspection_finding`
--
ALTER TABLE `zone_inspection_finding`
  ADD PRIMARY KEY (`finding_id`),
  ADD KEY `inspection_id` (`inspection_id`),
  ADD KEY `nutrient_code` (`nutrient_code`);

--
-- Indexes for table `zone_inspection_image`
--
ALTER TABLE `zone_inspection_image`
  ADD PRIMARY KEY (`image_id`),
  ADD KEY `inspection_id` (`inspection_id`);

--
-- Indexes for table `zone_inspection_recommendation`
--
ALTER TABLE `zone_inspection_recommendation`
  ADD PRIMARY KEY (`recommendation_id`),
  ADD KEY `inspection_id` (`inspection_id`),
  ADD KEY `fertilizer_id` (`fertilizer_id`),
  ADD KEY `nutrient_code` (`nutrient_code`),
  ADD KEY `idx_zir_inspection` (`inspection_id`),
  ADD KEY `idx_zir_nutrient` (`nutrient_code`);

--
-- AUTO_INCREMENT for dumped tables
--

--
-- AUTO_INCREMENT for table `fertilizer`
--
ALTER TABLE `fertilizer`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=48;

--
-- AUTO_INCREMENT for table `field`
--
ALTER TABLE `field`
  MODIFY `field_id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=16;

--
-- AUTO_INCREMENT for table `field_point`
--
ALTER TABLE `field_point`
  MODIFY `point_id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=97;

--
-- AUTO_INCREMENT for table `mark_zone`
--
ALTER TABLE `mark_zone`
  MODIFY `mark_id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=123;

--
-- AUTO_INCREMENT for table `password_reset_tokens`
--
ALTER TABLE `password_reset_tokens`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=16;

--
-- AUTO_INCREMENT for table `users`
--
ALTER TABLE `users`
  MODIFY `user_id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=12;

--
-- AUTO_INCREMENT for table `zone`
--
ALTER TABLE `zone`
  MODIFY `zone_id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=17;

--
-- AUTO_INCREMENT for table `zone_inspection`
--
ALTER TABLE `zone_inspection`
  MODIFY `inspection_id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=92;

--
-- AUTO_INCREMENT for table `zone_inspection_finding`
--
ALTER TABLE `zone_inspection_finding`
  MODIFY `finding_id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=82;

--
-- AUTO_INCREMENT for table `zone_inspection_image`
--
ALTER TABLE `zone_inspection_image`
  MODIFY `image_id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=127;

--
-- AUTO_INCREMENT for table `zone_inspection_recommendation`
--
ALTER TABLE `zone_inspection_recommendation`
  MODIFY `recommendation_id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=36;

--
-- Constraints for dumped tables
--

--
-- Constraints for table `field_point`
--
ALTER TABLE `field_point`
  ADD CONSTRAINT `field_point_ibfk_1` FOREIGN KEY (`field_id`) REFERENCES `field` (`field_id`) ON DELETE CASCADE;

--
-- Constraints for table `mark_zone`
--
ALTER TABLE `mark_zone`
  ADD CONSTRAINT `mark_zone_ibfk_1` FOREIGN KEY (`zone_id`) REFERENCES `zone` (`zone_id`) ON DELETE CASCADE;

--
-- Constraints for table `zone`
--
ALTER TABLE `zone`
  ADD CONSTRAINT `zone_ibfk_1` FOREIGN KEY (`field_id`) REFERENCES `field` (`field_id`) ON DELETE CASCADE;

--
-- Constraints for table `zone_inspection`
--
ALTER TABLE `zone_inspection`
  ADD CONSTRAINT `fk_inspection_field` FOREIGN KEY (`field_id`) REFERENCES `field` (`field_id`) ON DELETE CASCADE,
  ADD CONSTRAINT `fk_inspection_zone_in_field` FOREIGN KEY (`zone_id`,`field_id`) REFERENCES `zone` (`zone_id`, `field_id`) ON DELETE CASCADE;

--
-- Constraints for table `zone_inspection_finding`
--
ALTER TABLE `zone_inspection_finding`
  ADD CONSTRAINT `zone_inspection_finding_ibfk_1` FOREIGN KEY (`inspection_id`) REFERENCES `zone_inspection` (`inspection_id`) ON DELETE CASCADE,
  ADD CONSTRAINT `zone_inspection_finding_ibfk_2` FOREIGN KEY (`nutrient_code`) REFERENCES `nutrient_deficiency` (`nutrient_code`);

--
-- Constraints for table `zone_inspection_image`
--
ALTER TABLE `zone_inspection_image`
  ADD CONSTRAINT `zone_inspection_image_ibfk_1` FOREIGN KEY (`inspection_id`) REFERENCES `zone_inspection` (`inspection_id`) ON DELETE CASCADE;
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
