-- phpMyAdmin SQL Dump
-- version 5.2.1
-- https://www.phpmyadmin.net/
--
-- Host: 127.0.0.1
-- Generation Time: Sep 22, 2025 at 12:07 PM
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
-- Database: `dbcocoa`
--

-- --------------------------------------------------------

--
-- Table structure for table `fertilizer`
--

CREATE TABLE `fertilizer` (
  `fertilizer_id` int(11) NOT NULL,
  `fert_name` varchar(120) NOT NULL,
  `formulation` varchar(80) DEFAULT NULL,
  `description` text DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `fertilizer`
--

INSERT INTO `fertilizer` (`fertilizer_id`, `fert_name`, `formulation`, `description`) VALUES
(1, 'ืN', '46-0-0', 'เพิ่มไนโตรเจนอย่างรวดเร็ว'),
(2, 'P', '18-46-0', 'บูสต์ฟอสฟอรัส/ราก'),
(3, 'K', '0-0-60', 'เพิ่มโพแทสเซียม/คุณภาพผล'),
(4, 'Mg', '-', 'ปรับ Mg และค่า pH บางส่วน');

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
(4, 'a', 1200.00, 4, '2025-09-09 10:07:32'),
(7, 's', 1600.00, 4, '2025-09-09 16:38:51'),
(8, 'a', 166.00, 5, '2025-09-11 02:38:53'),
(9, 'B', 1666.00, 5, '2025-09-12 18:59:07'),
(10, 'ทดสอบนะ', 600.00, 5, '2025-09-14 08:38:12'),
(11, 'a', 1600.00, 7, '2025-09-16 18:28:47'),
(12, 'b', 1600.00, 7, '2025-09-21 18:00:30'),
(13, 'แปลง0', 201.00, 9, '2025-09-22 09:00:25');

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
(10, 'tai1', '652021054@tsu.ac.thf', '0215467857', '$2b$12$ZUgBuXFPaQF83oatN9WhyOYCjr9qPnAiot8bhHVBGtyP.g5PTOzSy', 'tai tai1', NULL, '2025-09-22 08:57:27', '2025-09-22 08:57:27');

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
(15, 'b2', 20, 12, '2025-09-22 10:05:54', 5);

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

--
-- Dumping data for table `zone_inspection`
--

INSERT INTO `zone_inspection` (`inspection_id`, `field_id`, `zone_id`, `round_no`, `inspected_at`, `inspector_user_id`, `method`, `status`, `notes`) VALUES
(22, 4, 2, 1, '2025-09-09 23:58:47', NULL, '', 'completed', '1'),
(23, 4, 2, 2, '2025-09-10 01:23:21', NULL, '', 'completed', '1'),
(24, 4, 2, 3, '2025-09-10 09:12:07', NULL, 'manual', '', '2'),
(25, 4, 2, 4, '2025-09-10 09:12:12', NULL, 'manual', '', '2'),
(26, 4, 2, 5, '2025-09-10 09:12:12', NULL, 'manual', '', '2'),
(27, 4, 2, 6, '2025-09-10 09:12:13', NULL, 'manual', '', '2'),
(28, 4, 2, 7, '2025-09-10 09:12:20', NULL, 'manual', '', '12'),
(29, 4, 2, 8, '2025-09-10 09:12:21', NULL, 'manual', '', '12'),
(30, 4, 2, 9, '2025-09-10 09:12:21', NULL, 'manual', '', '12'),
(31, 4, 2, 10, '2025-09-10 09:13:13', NULL, 'manual', '', '11'),
(32, 4, 2, 11, '2025-09-10 09:13:17', NULL, 'manual', '', '11'),
(33, 4, 2, 12, '2025-09-10 09:13:17', NULL, 'manual', '', '11'),
(34, 4, 2, 13, '2025-09-10 09:19:07', NULL, 'manual', '', '11'),
(35, 4, 2, 14, '2025-09-10 09:19:09', NULL, 'manual', '', '11'),
(36, 4, 2, 15, '2025-09-10 09:19:10', NULL, 'manual', '', '11'),
(37, 4, 2, 16, '2025-09-10 09:21:16', NULL, 'manual', '', '11'),
(38, 4, 2, 17, '2025-09-10 09:25:03', NULL, 'manual', '', '11'),
(39, 4, 2, 18, '2025-09-10 09:26:47', NULL, 'manual', '', '11'),
(40, 4, 2, 19, '2025-09-10 09:26:48', NULL, 'manual', '', '11'),
(41, 4, 2, 20, '2025-09-10 09:27:33', NULL, 'manual', '', '11'),
(42, 4, 2, 21, '2025-09-10 09:27:34', NULL, 'manual', '', '11'),
(43, 4, 4, 1, '2025-09-10 09:27:48', NULL, 'manual', '', '11'),
(44, 4, 4, 2, '2025-09-10 09:27:49', NULL, 'manual', '', '11'),
(45, 4, 4, 3, '2025-09-10 09:31:48', NULL, 'manual', '', '11'),
(46, 4, 4, 4, '2025-09-10 09:35:23', NULL, 'manual', 'pending', '11'),
(47, 4, 2, 22, '2025-09-10 09:44:28', NULL, 'manual', 'pending', '222'),
(48, 4, 2, 23, '2025-09-10 09:47:35', NULL, 'manual', 'pending', '222'),
(49, 4, 2, 24, '2025-09-10 09:47:41', NULL, 'manual', 'pending', '222'),
(50, 4, 2, 25, '2025-09-10 09:53:37', NULL, 'manual', 'pending', '11'),
(51, 4, 4, 5, '2025-09-10 09:56:24', NULL, 'manual', 'pending', '22'),
(52, 4, 4, 6, '2025-09-10 09:58:53', NULL, 'manual', 'pending', '22'),
(53, 4, 4, 7, '2025-09-10 10:01:25', NULL, 'manual', 'pending', '111'),
(54, 4, 2, 26, '2025-09-10 10:04:29', NULL, 'manual', 'completed', '22'),
(55, 7, 5, 1, '2025-09-10 10:06:47', NULL, 'manual', 'pending', '22'),
(56, 4, 4, 8, '2025-09-10 10:17:24', NULL, 'manual', '', '22'),
(57, 4, 2, 27, '2025-09-11 00:54:20', NULL, 'manual', '', 'aa'),
(58, 4, 2, 28, '2025-09-11 01:04:39', NULL, 'manual', '', '111'),
(59, 4, 2, 29, '2025-09-11 01:25:13', NULL, 'manual', '', '12'),
(60, 4, 3, 1, '2025-09-11 02:18:29', NULL, 'manual', 'pending', '12'),
(61, 4, 2, 30, '2025-09-11 03:15:16', 4, '', '', '11'),
(62, 8, 6, 1, '2025-09-11 09:39:15', NULL, 'manual', 'completed', '1'),
(63, 8, 6, 2, '2025-09-11 22:45:29', NULL, 'manual', 'completed', '11'),
(64, 8, 6, 3, '2025-09-11 22:49:26', NULL, 'manual', 'completed', '11'),
(65, 8, 6, 4, '2025-09-12 00:44:46', NULL, 'manual', 'completed', '11'),
(66, 8, 6, 5, '2025-09-12 01:11:16', NULL, 'manual', 'completed', '11'),
(67, 8, 6, 6, '2025-09-12 23:09:35', NULL, 'manual', 'pending', '22'),
(68, 9, 7, 1, '2025-09-13 01:59:37', NULL, 'manual', 'pending', NULL),
(69, 10, 8, 1, '2025-09-14 15:43:22', NULL, 'manual', 'pending', NULL),
(70, 11, 9, 1, '2025-09-17 01:29:38', NULL, 'manual', 'completed', NULL),
(71, 11, 9, 2, '2025-09-18 21:41:56', NULL, 'manual', 'completed', NULL),
(72, 11, 9, 3, '2025-09-18 22:33:42', NULL, 'manual', 'pending', NULL),
(73, 13, 13, 1, '2025-09-22 16:23:18', NULL, 'manual', 'completed', NULL),
(74, 13, 13, 2, '2025-09-22 16:27:21', NULL, 'manual', 'pending', NULL);

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

--
-- Dumping data for table `zone_inspection_finding`
--

INSERT INTO `zone_inspection_finding` (`finding_id`, `inspection_id`, `nutrient_code`, `severity`, `confidence`, `area_percent`, `trees_affected`, `notes`) VALUES
(3, 22, 'Mg', 'severe', 95.71, NULL, NULL, 'aggregated from 1 detection(s)/image(s)'),
(4, 23, 'Mg', 'severe', 95.71, NULL, NULL, 'aggregated from 1 detection(s)/image(s)'),
(5, 54, 'N', 'moderate', 85.00, NULL, NULL, 'analyze stub'),
(6, 54, 'K', 'mild', 72.00, NULL, NULL, 'analyze stub'),
(12, 60, 'N', 'moderate', 82.00, NULL, NULL, 'auto-generated'),
(22, 64, 'Mg', 'severe', 95.70, NULL, NULL, NULL),
(23, 64, 'K', 'severe', 92.51, NULL, NULL, NULL),
(24, 64, 'N', 'moderate', 75.17, NULL, NULL, NULL),
(25, 64, 'P', 'mild', 36.44, NULL, NULL, NULL),
(34, 65, 'N', 'severe', 86.66, NULL, NULL, NULL),
(35, 65, 'K', 'severe', 92.51, NULL, NULL, NULL),
(36, 66, 'K', 'severe', 93.07, NULL, NULL, NULL),
(42, 68, 'Mg', 'severe', 95.71, NULL, NULL, NULL),
(43, 67, 'Mg', 'severe', 95.70, NULL, NULL, NULL),
(44, 67, 'K', 'severe', 92.51, NULL, NULL, NULL),
(45, 69, 'N', 'moderate', 79.96, NULL, NULL, NULL),
(48, 70, 'Mg', 'severe', 95.70, NULL, NULL, NULL),
(49, 70, 'K', 'severe', 92.51, NULL, NULL, NULL),
(50, 70, 'N', 'severe', 86.66, NULL, NULL, NULL),
(54, 71, 'N', 'moderate', 75.17, NULL, NULL, NULL),
(58, 73, 'N', 'severe', 86.66, NULL, NULL, NULL),
(59, 73, 'P', 'mild', 36.44, NULL, NULL, NULL),
(60, 73, 'K', 'severe', 92.51, NULL, NULL, NULL),
(61, 74, 'N', 'severe', 86.66, NULL, NULL, NULL),
(62, 74, 'K', 'severe', 92.51, NULL, NULL, NULL),
(63, 74, 'P', 'mild', 36.44, NULL, NULL, NULL);

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
-- Dumping data for table `zone_inspection_image`
--

INSERT INTO `zone_inspection_image` (`image_id`, `inspection_id`, `image_path`, `captured_at`, `meta`, `file_name`, `file_path`, `created_at`) VALUES
(6, 22, 'inspections/22/20250909_165854_755377_mg.png', '2025-09-09 23:58:54', '{\"original_name\": \"mg.png\", \"saved_name\": \"20250909_165854_755377_mg.png\", \"saved_at_utc\": \"20250909_165854_755377\", \"model\": \"best (1).pt\"}', '20250909_165854_755377_mg.png', 'inspections/22/20250909_165854_755377_mg.png', '2025-09-09 23:58:54'),
(7, 23, 'inspections/23/20250909_182333_510204_mg.png', '2025-09-10 01:23:33', '{\"original_name\": \"mg.png\", \"saved_name\": \"20250909_182333_510204_mg.png\", \"saved_at_utc\": \"20250909_182333_510204\", \"model\": \"best (1).pt\"}', '20250909_182333_510204_mg.png', 'inspections/23/20250909_182333_510204_mg.png', '2025-09-10 01:23:33'),
(8, 54, 'inspections/54/036a27b3cdb344b88cfd0e918fbc26ab.png', '2025-09-10 10:22:20', '{\"original_name\": \"mg.png\", \"saved_name\": \"036a27b3cdb344b88cfd0e918fbc26ab.png\"}', '036a27b3cdb344b88cfd0e918fbc26ab.png', 'inspections/54/036a27b3cdb344b88cfd0e918fbc26ab.png', '2025-09-10 10:22:20'),
(9, 50, 'inspections\\50\\50_20250910184309396731.png', '2025-09-11 01:43:09', '{\"original_name\": \"mg.png\", \"saved_name\": \"50_20250910184309396731.png\", \"saved_at_utc\": \"20250910184309396731\"}', NULL, NULL, NULL),
(10, 53, 'inspections\\53\\53_20250910190411282932.png', '2025-09-11 02:04:11', '{\"original_name\": \"mg.png\", \"saved_name\": \"53_20250910190411282932.png\", \"saved_at_utc\": \"20250910190411282932\"}', NULL, NULL, NULL),
(11, 53, 'inspections\\53\\53_20250910190430722184.png', '2025-09-11 02:04:30', '{\"original_name\": \"p.png\", \"saved_name\": \"53_20250910190430722184.png\", \"saved_at_utc\": \"20250910190430722184\"}', NULL, NULL, NULL),
(12, 50, 'inspections\\50\\50_20250910191115449515.png', '2025-09-11 02:11:15', '{\"original_name\": \"mg.png\", \"saved_name\": \"50_20250910191115449515.png\", \"saved_at_utc\": \"20250910191115449515\"}', NULL, NULL, NULL),
(13, 60, 'inspections\\60\\60_20250910191836373357.png', '2025-09-11 02:18:36', '{\"original_name\": \"p.png\", \"saved_name\": \"60_20250910191836373357.png\", \"saved_at_utc\": \"20250910191836373357\"}', NULL, NULL, NULL),
(14, 60, 'inspections\\60\\60_20250910192023398106.png', '2025-09-11 02:20:23', '{\"original_name\": \"p2.png\", \"saved_name\": \"60_20250910192023398106.png\", \"saved_at_utc\": \"20250910192023398106\"}', NULL, NULL, NULL),
(15, 50, 'inspections\\50\\50_20250910193951602261.png', '2025-09-11 02:39:51', '{\"original_name\": \"mg.png\", \"saved_name\": \"50_20250910193951602261.png\", \"saved_at_utc\": \"20250910193951602261\"}', NULL, NULL, NULL),
(16, 53, 'inspections\\53\\53_20250910194556292235.png', '2025-09-11 02:45:56', '{\"original_name\": \"mg.png\", \"saved_name\": \"53_20250910194556292235.png\", \"saved_at_utc\": \"20250910194556292235\"}', NULL, NULL, NULL),
(17, 53, 'inspections\\53\\53_20250910194729628296.png', '2025-09-11 02:47:29', '{\"original_name\": \"p.png\", \"saved_name\": \"53_20250910194729628296.png\", \"saved_at_utc\": \"20250910194729628296\"}', NULL, NULL, NULL),
(18, 53, 'inspections\\53\\53_20250910194741004056.png', '2025-09-11 02:47:41', '{\"original_name\": \"p.png\", \"saved_name\": \"53_20250910194741004056.png\", \"saved_at_utc\": \"20250910194741004056\"}', NULL, NULL, NULL),
(19, 61, 'inspection_61\\20250911_031526_095990.png', '2025-09-11 03:15:26', NULL, NULL, NULL, NULL),
(20, 50, 'inspections\\50\\50_20250910201712513209.png', '2025-09-11 03:17:12', '{\"original_name\": \"mg.png\", \"saved_name\": \"50_20250910201712513209.png\", \"saved_at_utc\": \"20250910201712513209\"}', NULL, NULL, NULL),
(21, 50, 'inspections\\50\\50_20250910201727843012.png', '2025-09-11 03:17:27', '{\"original_name\": \"mg.png\", \"saved_name\": \"50_20250910201727843012.png\", \"saved_at_utc\": \"20250910201727843012\"}', NULL, NULL, NULL),
(22, 62, 'inspections\\62\\62_20250911023924630673.png', '2025-09-11 09:39:24', '{\"original_name\": \"p.png\", \"saved_name\": \"62_20250911023924630673.png\", \"saved_at_utc\": \"20250911023924630673\"}', NULL, NULL, NULL),
(23, 62, 'inspections\\62\\62_20250911024326057869.png', '2025-09-11 09:43:26', '{\"original_name\": \"p.png\", \"saved_name\": \"62_20250911024326057869.png\", \"saved_at_utc\": \"20250911024326057869\"}', NULL, NULL, NULL),
(24, 62, 'inspections\\62\\62_20250911025222853193.png', '2025-09-11 09:52:22', '{\"original_name\": \"mg.png\", \"saved_name\": \"62_20250911025222853193.png\", \"saved_at_utc\": \"20250911025222853193\"}', NULL, NULL, NULL),
(25, 62, 'inspections\\62\\62_20250911031557505403.png', '2025-09-11 10:15:57', '{\"original_name\": \"p.png\", \"saved_name\": \"62_20250911031557505403.png\", \"saved_at_utc\": \"20250911031557505403\"}', NULL, NULL, NULL),
(26, 62, 'inspections\\62\\62_20250911032657089896.png', '2025-09-11 10:26:57', '{\"original_name\": \"mg.png\", \"saved_name\": \"62_20250911032657089896.png\", \"saved_at_utc\": \"20250911032657089896\"}', NULL, NULL, NULL),
(27, 63, 'inspections\\63\\63_20250911154539190264.png', '2025-09-11 22:45:39', '{\"original_name\": \"mg.png\", \"saved_name\": \"63_20250911154539190264.png\", \"saved_at_utc\": \"20250911154539190264\"}', NULL, NULL, NULL),
(28, 63, 'inspections\\63\\63_20250911154817724934.png', '2025-09-11 22:48:17', '{\"original_name\": \"mg.png\", \"saved_name\": \"63_20250911154817724934.png\", \"saved_at_utc\": \"20250911154817724934\"}', NULL, NULL, NULL),
(29, 64, 'inspections\\64\\64_20250911154933700167.png', '2025-09-11 22:49:33', '{\"original_name\": \"mg.png\", \"saved_name\": \"64_20250911154933700167.png\", \"saved_at_utc\": \"20250911154933700167\"}', NULL, NULL, NULL),
(30, 64, 'inspections/64/64_20250911174113597444.png', '2025-09-12 00:41:13', '{\"original_name\": \"mg.png\", \"saved_name\": \"64_20250911174113597444.png\", \"saved_at_utc\": \"20250911174113597444\"}', NULL, NULL, NULL),
(31, 64, 'inspections/64/64_20250911174149603490.png', '2025-09-12 00:41:49', '{\"original_name\": \"p.png\", \"saved_name\": \"64_20250911174149603490.png\", \"saved_at_utc\": \"20250911174149603490\"}', NULL, NULL, NULL),
(32, 64, 'inspections/64/64_20250911174226887764.png', '2025-09-12 00:42:26', '{\"original_name\": \"p2.png\", \"saved_name\": \"64_20250911174226887764.png\", \"saved_at_utc\": \"20250911174226887764\"}', NULL, NULL, NULL),
(33, 64, 'inspections/64/64_20250911174258523534.jpg', '2025-09-12 00:42:58', '{\"original_name\": \"26040.jpg\", \"saved_name\": \"64_20250911174258523534.jpg\", \"saved_at_utc\": \"20250911174258523534\"}', NULL, NULL, NULL),
(34, 65, 'inspections/65/65_20250911174518350210.png', '2025-09-12 00:45:18', '{\"original_name\": \"10.png\", \"saved_name\": \"65_20250911174518350210.png\", \"saved_at_utc\": \"20250911174518350210\"}', NULL, NULL, NULL),
(35, 65, 'inspections/65/65_20250911174543405448.jpg', '2025-09-12 00:45:43', '{\"original_name\": \"26040.jpg\", \"saved_name\": \"65_20250911174543405448.jpg\", \"saved_at_utc\": \"20250911174543405448\"}', NULL, NULL, NULL),
(36, 65, 'inspections/65/65_20250911174558329034.png', '2025-09-12 00:45:58', '{\"original_name\": \"k3.png\", \"saved_name\": \"65_20250911174558329034.png\", \"saved_at_utc\": \"20250911174558329034\"}', NULL, NULL, NULL),
(37, 65, 'inspections/65/65_20250911174613648717.jpg', '2025-09-12 00:46:13', '{\"original_name\": \"26040.jpg\", \"saved_name\": \"65_20250911174613648717.jpg\", \"saved_at_utc\": \"20250911174613648717\"}', NULL, NULL, NULL),
(38, 65, 'inspections/65/65_20250911174642286201.jpg', '2025-09-12 00:46:42', '{\"original_name\": \"26017.jpg\", \"saved_name\": \"65_20250911174642286201.jpg\", \"saved_at_utc\": \"20250911174642286201\"}', NULL, NULL, NULL),
(39, 66, 'inspections/66/66_20250911181123785697.jpg', '2025-09-12 01:11:23', '{\"original_name\": \"25998.jpg\", \"saved_name\": \"66_20250911181123785697.jpg\", \"saved_at_utc\": \"20250911181123785697\"}', NULL, NULL, NULL),
(40, 66, 'inspections/66/66_20250911181147261346.jpg', '2025-09-12 01:11:47', '{\"original_name\": \"25274_0.jpg\", \"saved_name\": \"66_20250911181147261346.jpg\", \"saved_at_utc\": \"20250911181147261346\"}', NULL, NULL, NULL),
(41, 66, 'inspections/66/66_20250911184246239857.png', '2025-09-12 01:42:46', '{\"original_name\": \"mg.png\", \"saved_name\": \"66_20250911184246239857.png\", \"saved_at_utc\": \"20250911184246239857\"}', NULL, NULL, NULL),
(42, 66, 'inspections/66/66_20250912153641086010.png', '2025-09-12 22:36:41', '{\"original_name\": \"mg.png\", \"saved_name\": \"66_20250912153641086010.png\", \"saved_at_utc\": \"20250912153641086010\"}', NULL, NULL, NULL),
(43, 66, 'inspections/66/66_20250912154534012995.png', '2025-09-12 22:45:34', '{\"original_name\": \"mg.png\", \"saved_name\": \"66_20250912154534012995.png\", \"saved_at_utc\": \"20250912154534012995\"}', NULL, NULL, NULL),
(44, 67, 'inspections/67/67_20250912160941977171.png', '2025-09-12 23:09:41', '{\"original_name\": \"mg.png\", \"saved_name\": \"67_20250912160941977171.png\", \"saved_at_utc\": \"20250912160941977171\"}', NULL, NULL, NULL),
(45, 67, 'inspections/67/67_20250912181020839737.png', '2025-09-13 01:10:20', '{\"original_name\": \"p.png\", \"saved_name\": \"67_20250912181020839737.png\", \"saved_at_utc\": \"20250912181020839737\"}', NULL, NULL, NULL),
(46, 68, 'inspections/68/68_20250912185945357659.png', '2025-09-13 01:59:45', '{\"original_name\": \"mg.png\", \"saved_name\": \"68_20250912185945357659.png\", \"saved_at_utc\": \"20250912185945357659\"}', NULL, NULL, NULL),
(47, 67, 'inspections/67/67_20250914062554020813.png', '2025-09-14 13:25:54', '{\"original_name\": \"p.png\", \"saved_name\": \"67_20250914062554020813.png\", \"saved_at_utc\": \"20250914062554020813\"}', NULL, NULL, NULL),
(48, 69, 'inspections/69/69_20250914085114382354.jpg', '2025-09-14 15:51:14', '{\"original_name\": \"JPEG_20250914_155036_8889541459276801248.jpg\", \"saved_name\": \"69_20250914085114382354.jpg\", \"saved_at_utc\": \"20250914085114382354\"}', NULL, NULL, NULL),
(49, 69, 'inspections/69/69_20250914085207234804.jpg', '2025-09-14 15:52:07', '{\"original_name\": \"JPEG_20250914_155152_1156796202011939803.jpg\", \"saved_name\": \"69_20250914085207234804.jpg\", \"saved_at_utc\": \"20250914085207234804\"}', NULL, NULL, NULL),
(50, 69, 'inspections/69/69_20250914085224066113.jpg', '2025-09-14 15:52:24', '{\"original_name\": \"JPEG_20250914_155220_8667599919588413213.jpg\", \"saved_name\": \"69_20250914085224066113.jpg\", \"saved_at_utc\": \"20250914085224066113\"}', NULL, NULL, NULL),
(51, 70, 'inspections/70/70_20250916182948682519.png', '2025-09-17 01:29:48', '{\"original_name\": \"mg.png\", \"saved_name\": \"70_20250916182948682519.png\", \"saved_at_utc\": \"20250916182948682519\"}', NULL, NULL, NULL),
(52, 70, 'inspections/70/70_20250916182948691417.png', '2025-09-17 01:29:48', '{\"original_name\": \"p.png\", \"saved_name\": \"70_20250916182948691417.png\", \"saved_at_utc\": \"20250916182948691417\"}', NULL, NULL, NULL),
(53, 70, 'inspections/70/70_20250918143203869957.png', '2025-09-18 21:32:03', '{\"original_name\": \"10.png\", \"saved_name\": \"70_20250918143203869957.png\", \"saved_at_utc\": \"20250918143203869957\"}', NULL, NULL, NULL),
(54, 70, 'inspections/70/70_20250918143203882975.jpg', '2025-09-18 21:32:03', '{\"original_name\": \"26040.jpg\", \"saved_name\": \"70_20250918143203882975.jpg\", \"saved_at_utc\": \"20250918143203882975\"}', NULL, NULL, NULL),
(55, 70, 'inspections/70/70_20250918143203885122.png', '2025-09-18 21:32:03', '{\"original_name\": \"k3.png\", \"saved_name\": \"70_20250918143203885122.png\", \"saved_at_utc\": \"20250918143203885122\"}', NULL, NULL, NULL),
(56, 71, 'inspections/71/71_20250918144203029982.jpg', '2025-09-18 21:42:03', '{\"original_name\": \"26040.jpg\", \"saved_name\": \"71_20250918144203029982.jpg\", \"saved_at_utc\": \"20250918144203029982\"}', NULL, NULL, NULL),
(57, 71, 'inspections/71/71_20250918144231259520.jpg', '2025-09-18 21:42:31', '{\"original_name\": \"26001.jpg\", \"saved_name\": \"71_20250918144231259520.jpg\", \"saved_at_utc\": \"20250918144231259520\"}', NULL, NULL, NULL),
(58, 71, 'inspections/71/71_20250918150248719635.jpg', '2025-09-18 22:02:48', '{\"original_name\": \"26000.jpg\", \"saved_name\": \"71_20250918150248719635.jpg\", \"saved_at_utc\": \"20250918150248719635\"}', NULL, NULL, NULL),
(59, 71, 'inspections/71/71_20250918151802761983.jpg', '2025-09-18 22:18:02', '{\"original_name\": \"26000.jpg\", \"saved_name\": \"71_20250918151802761983.jpg\", \"saved_at_utc\": \"20250918151802761983\"}', NULL, NULL, NULL),
(60, 73, 'inspections/73/73_20250922092454588556.jpg', '2025-09-22 16:24:54', '{\"original_name\": \"26014.jpg\", \"saved_name\": \"73_20250922092454588556.jpg\", \"saved_at_utc\": \"20250922092454588556\"}', NULL, NULL, NULL),
(61, 73, 'inspections/73/73_20250922092454593781.png', '2025-09-22 16:24:54', '{\"original_name\": \"scaled_m6.png\", \"saved_name\": \"73_20250922092454593781.png\", \"saved_at_utc\": \"20250922092454593781\"}', NULL, NULL, NULL),
(62, 73, 'inspections/73/73_20250922092454595251.png', '2025-09-22 16:24:54', '{\"original_name\": \"p2.png\", \"saved_name\": \"73_20250922092454595251.png\", \"saved_at_utc\": \"20250922092454595251\"}', NULL, NULL, NULL),
(63, 73, 'inspections/73/73_20250922092454596642.png', '2025-09-22 16:24:54', '{\"original_name\": \"10.png\", \"saved_name\": \"73_20250922092454596642.png\", \"saved_at_utc\": \"20250922092454596642\"}', NULL, NULL, NULL),
(64, 73, 'inspections/73/73_20250922092454597863.png', '2025-09-22 16:24:54', '{\"original_name\": \"k3.png\", \"saved_name\": \"73_20250922092454597863.png\", \"saved_at_utc\": \"20250922092454597863\"}', NULL, NULL, NULL),
(65, 74, 'inspections/74/74_20250922092729092090.png', '2025-09-22 16:27:29', '{\"original_name\": \"10.png\", \"saved_name\": \"74_20250922092729092090.png\", \"saved_at_utc\": \"20250922092729092090\"}', NULL, NULL, NULL),
(66, 74, 'inspections/74/74_20250922092729094211.jpg', '2025-09-22 16:27:29', '{\"original_name\": \"26040.jpg\", \"saved_name\": \"74_20250922092729094211.jpg\", \"saved_at_utc\": \"20250922092729094211\"}', NULL, NULL, NULL),
(67, 74, 'inspections/74/74_20250922092729096018.png', '2025-09-22 16:27:29', '{\"original_name\": \"k3.png\", \"saved_name\": \"74_20250922092729096018.png\", \"saved_at_utc\": \"20250922092729096018\"}', NULL, NULL, NULL),
(68, 74, 'inspections/74/74_20250922092729098473.png', '2025-09-22 16:27:29', '{\"original_name\": \"m6.png\", \"saved_name\": \"74_20250922092729098473.png\", \"saved_at_utc\": \"20250922092729098473\"}', NULL, NULL, NULL),
(69, 74, 'inspections/74/74_20250922092729100807.png', '2025-09-22 16:27:29', '{\"original_name\": \"p2.png\", \"saved_name\": \"74_20250922092729100807.png\", \"saved_at_utc\": \"20250922092729100807\"}', NULL, NULL, NULL);

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
(18, 74, 2, 'P', 'บูสต์ฟอสฟอรัส/ราก', NULL, NULL, 'suggested', NULL, '2025-09-22 09:27:30');

--
-- Indexes for dumped tables
--

--
-- Indexes for table `fertilizer`
--
ALTER TABLE `fertilizer`
  ADD PRIMARY KEY (`fertilizer_id`);

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
  ADD KEY `nutrient_code` (`nutrient_code`);

--
-- AUTO_INCREMENT for dumped tables
--

--
-- AUTO_INCREMENT for table `fertilizer`
--
ALTER TABLE `fertilizer`
  MODIFY `fertilizer_id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=5;

--
-- AUTO_INCREMENT for table `field`
--
ALTER TABLE `field`
  MODIFY `field_id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=15;

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
  MODIFY `user_id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=11;

--
-- AUTO_INCREMENT for table `zone`
--
ALTER TABLE `zone`
  MODIFY `zone_id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=16;

--
-- AUTO_INCREMENT for table `zone_inspection`
--
ALTER TABLE `zone_inspection`
  MODIFY `inspection_id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=75;

--
-- AUTO_INCREMENT for table `zone_inspection_finding`
--
ALTER TABLE `zone_inspection_finding`
  MODIFY `finding_id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=64;

--
-- AUTO_INCREMENT for table `zone_inspection_image`
--
ALTER TABLE `zone_inspection_image`
  MODIFY `image_id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=70;

--
-- AUTO_INCREMENT for table `zone_inspection_recommendation`
--
ALTER TABLE `zone_inspection_recommendation`
  MODIFY `recommendation_id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=19;

--
-- Constraints for dumped tables
--

--
-- Constraints for table `field`
--
ALTER TABLE `field`
  ADD CONSTRAINT `field_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`user_id`) ON DELETE CASCADE;

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

--
-- Constraints for table `zone_inspection_recommendation`
--
ALTER TABLE `zone_inspection_recommendation`
  ADD CONSTRAINT `zone_inspection_recommendation_ibfk_1` FOREIGN KEY (`inspection_id`) REFERENCES `zone_inspection` (`inspection_id`) ON DELETE CASCADE,
  ADD CONSTRAINT `zone_inspection_recommendation_ibfk_2` FOREIGN KEY (`fertilizer_id`) REFERENCES `fertilizer` (`fertilizer_id`),
  ADD CONSTRAINT `zone_inspection_recommendation_ibfk_3` FOREIGN KEY (`nutrient_code`) REFERENCES `nutrient_deficiency` (`nutrient_code`);
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
