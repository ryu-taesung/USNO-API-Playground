#include <boost/date_time/c_local_time_adjustor.hpp>
#include <boost/date_time/local_time/local_time.hpp>
#include <boost/date_time/posix_time/posix_time.hpp>
#include <boost/format.hpp>
#include <boost/json/src.hpp>
#include <boost/property_tree/ptree.hpp>
#include <boost/property_tree/xml_parser.hpp>
#include <chrono>
#include <iomanip>
#include <iostream>
#include <regex>
#include <sstream>
#include <string>
#include <thread>

#include "HttpClient.hpp"
#include "load_tz_data.hpp"

std::string buildApiUrl(const std::string& date, const std::string& lat_long) {
  boost::format fmter(
      "https://aa.usno.navy.mil/api/rstt/oneday?date=%1%&coords=%2%");
  fmter % date % lat_long;
  return fmter.str();
}

std::string buildWeatherApiUrl(const std::string& lat_long) {
  boost::format fmter("https://api.weather.gov/points/%1%");
  fmter % lat_long;
  return fmter.str();
}

std::string dateToString(const boost::gregorian::date& date) {
  return boost::gregorian::to_iso_extended_string(date);
}

boost::json::object parseJson(const std::string& json_result) {
  try {
    boost::json::value parsed_data = boost::json::parse(json_result);
    auto data_object = parsed_data.as_object()
                           .at("properties")
                           .as_object()
                           .at("data")
                           .as_object();

    return data_object;

  } catch (const std::exception& e) {
    std::cerr << "JSON parsing error: " << e.what() << std::endl;
    throw;
  }
}

std::string getLatLong(std::string zipXML) {
  std::string output;
  std::stringstream ss;
  try {
    ss << zipXML;
    boost::property_tree::ptree pt;
    read_xml(ss, pt);
    output = pt.get<std::string>("dwml.latLonList");
  } catch (const std::exception& e) {
    std::cerr << "Error determining lat/long from zip code.\n";
    std::cerr << "Error: " << e.what() << std::endl;
  }
  return output;
}

std::string getZipCode() {
  std::string zipCode{};
  std::regex zipCodeTest(R"(^\d{5,5}$)");
  do {
    std::cout << "Enter ZIP code: ";
    std::cin >> zipCode;
  } while (!std::regex_search(zipCode, zipCodeTest));
  return zipCode;
}

std::string zip_to_lat_long(HttpClient& httpClient, std::string zipCode) {
  std::cout << "Getting Lat/Long from ZIP code. . . ";
  std::string zipXMLUrl{
      "https://graphical.weather.gov/xml/sample_products/browser_interface/"
      "ndfdXMLclient.php?listZipCodeList="};
  std::string zipXML = httpClient.get(zipXMLUrl + zipCode);
  std::string lat_long = getLatLong(zipXML);
  if (lat_long == ",") throw std::runtime_error("Invalid ZIP code!\n");
  if (lat_long.empty()) throw std::runtime_error("Lat/Long XML Failure!\n");
  std::cout << lat_long << "\n";
  return lat_long;
}

std::string generateISODateString(int year, int month, int day) {
  std::stringstream ss;
  ss << year << "-" << std::setw(2) << std::setfill('0') << month << "-";
  ss << std::setw(2) << std::setfill('0') << day << "T";
  return ss.str();
}

std::string getTimezoneFromLatLong(std::string lat_long) try {
  HttpClient httpClient;
  std::string json = httpClient.get(buildWeatherApiUrl(lat_long));
  boost::json::value parsed_data = boost::json::parse(json);
  std::string time_zone = parsed_data.as_object()
                              .at("properties")
                              .as_object()
                              .at("timeZone")
                              .as_string()
                              .c_str();
  return time_zone;
} catch (const std::exception& e) {
  std::stringstream out;
  out << "Exception: " << e.what();
  return out.str();
}

int main(int argc, char* argv[]) try {
  HttpClient httpClient;
  std::string zipCode = getZipCode();
  std::string lat_long = zip_to_lat_long(httpClient, zipCode);

  // Calculate date range
  using namespace boost::posix_time;
  using namespace boost::gregorian;
  using namespace std::literals::chrono_literals;
  ptime now = second_clock::local_time();
  date currentDate = now.date();
  int daysRange = 4;  // Default range of days

  boost::local_time::tz_database tz_db;
  // tz_db.load_from_file("date_time_zonespec.csv");
  tz_db.load_from_stream(TZ_DB);
  auto timezone = getTimezoneFromLatLong(lat_long);
  std::cout << "Using timezone: " << timezone << "\n\n";
  boost::local_time::time_zone_ptr tz = tz_db.time_zone_from_region(timezone);

  // create stringstream outside of loops for reuse
  std::stringstream ss;
  bool useLocalTime{false};
  if (argc == 2) {
    if (std::string(argv[1]) == "1")
      useLocalTime = true;
    else
      useLocalTime = false;
  }
  if (!useLocalTime) {
    ss.imbue(std::locale(std::locale::classic(),
                         new boost::local_time::local_time_facet("%H:%M")));
  } else {
    ss.imbue(std::locale(std::locale::classic(),
                         new boost::posix_time::time_facet("%H:%M")));
  }
  typedef boost::date_time::c_local_adjustor<boost::posix_time::ptime>
      local_adj;

  for (int i = 0; i < daysRange; ++i) {
    date targetDate = currentDate + days(i);
    std::string dateString = dateToString(targetDate);
    std::string api_url = buildApiUrl(dateString, lat_long);

    // std::cout << "API URL for " << dateString << ": " << api_url << '\n';
    std::string json_result = httpClient.get(api_url);
    // std::cout << "JSON Result: " << json_result << '\n';

    boost::json::object properties = parseJson(json_result);

    std::string utc_date = generateISODateString(
        properties.at("year").as_int64(), properties.at("month").as_int64(),
        properties.at("day").as_int64());

    // Loop through sundata array
    auto sundata_array = properties.at("sundata").as_array();
    std::string sunrise_time;
    std::string sunset_time;

    for (const auto& item : sundata_array) {
      std::string phen = item.as_object().at("phen").as_string().c_str();
      std::string time =
          utc_date + item.as_object().at("time").as_string().c_str();
      // std::cout << time << '\n';
      boost::posix_time::ptime utc_dtg =
          boost::posix_time::from_iso_extended_string(time);

      if (phen == "Rise") {
        boost::local_time::local_date_time sunrise_local_dt(utc_dtg, tz);
        boost::posix_time::ptime myLocal = local_adj::utc_to_local(utc_dtg);
        if (!useLocalTime) {
          ss << sunrise_local_dt;
        } else {
          ss << myLocal;
        }
        sunrise_time = ss.str();
        // Clear the stringstream for reuse
        ss.str("");
        ss.clear();
      } else if (phen == "Set") {
        boost::local_time::local_date_time sunset_local_dt(utc_dtg, tz);
        boost::posix_time::ptime myLocal = local_adj::utc_to_local(utc_dtg);
        if (!useLocalTime) {
          ss << sunset_local_dt;
        } else {
          ss << myLocal;
        }
        sunset_time = ss.str();
        // Clear the stringstream for reuse
        ss.str("");
        ss.clear();
      }
    }
    std::cout << properties.at("year").as_int64() << '-' << std::setw(2)
              << std::setfill('0') << properties.at("month").as_int64() << '-'
              << std::setw(2) << std::setfill('0')
              << properties.at("day").as_int64() << " - "
              << properties.at("day_of_week").as_string().c_str() << '\n';
    std::cout << "Sunrise: " << sunrise_time << ", Sunset: " << sunset_time
              << '\n';
    std::cout << "Moon Phase: " << properties.at("curphase").as_string().c_str()
              << " (" << properties.at("fracillum").as_string().c_str() << ")\n"
              << '\n';

    // Sleep for 1 second between API calls
    std::this_thread::sleep_for(1s);
  }

} catch (const std::exception& e) {
  std::cerr << "Error: " << e.what() << std::endl;
}