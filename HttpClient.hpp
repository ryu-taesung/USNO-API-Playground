#pragma once

#include <curl/curl.h>
#include <sstream>

namespace {
  size_t writeFunction(void* ptr, size_t size, size_t nmemb, std::string* data) {
    data->append((char*)ptr, size * nmemb);
    return size * nmemb;
  }
}

class HttpClient {
 private:
  std::string curl_version;
  std::string user_agent_string; // Computed once during initialization

  // Reference counting for instances
  static int instance_count;

 public:
  HttpClient() 
      : curl_version(get_curl_version()),
        user_agent_string("rts C++ client with libcurl/" + curl_version) {
    if (instance_count == 0) {
      // Initialize the curl library only for the first instance
      curl_global_init(CURL_GLOBAL_DEFAULT);
    }
    ++instance_count; // Increase the instance count
  }

  HttpClient(const HttpClient& other)
      : curl_version(other.curl_version),
        user_agent_string(other.user_agent_string) {
    ++instance_count; // Increase the instance count for copy constructor
  }

  HttpClient& operator=(const HttpClient& other) {
    if (this != &other) {
      curl_version = other.curl_version;
      user_agent_string = other.user_agent_string;
      ++instance_count; // Increase the instance count for copy assignment
    }
    return *this;
  }

  ~HttpClient() {
    --instance_count; // Decrease the instance count
    if (instance_count == 0) {
      // Cleanup the curl library only when the last instance is destroyed
      curl_global_cleanup();
    }
  }

  std::string get(const std::string& url) {
    auto curl = curl_easy_init();
    if (!curl) {
      throw std::runtime_error("Failed to initialize cURL for URL: " + url);
    }

    std::string response_string;
    curl_easy_setopt(curl, CURLOPT_URL, url.c_str());
    curl_easy_setopt(curl, CURLOPT_NOPROGRESS, 1L);
    curl_easy_setopt(curl, CURLOPT_USERAGENT, user_agent_string.c_str());
    curl_easy_setopt(curl, CURLOPT_WRITEFUNCTION, writeFunction);
    curl_easy_setopt(curl, CURLOPT_WRITEDATA, &response_string);

    auto ret = curl_easy_perform(curl);
    if (ret != CURLE_OK) {
      curl_easy_cleanup(curl); // Ensure proper cleanup
      throw std::runtime_error("cURL error for URL " + url + ": " + curl_easy_strerror(ret));
    }

    curl_easy_cleanup(curl);
    return response_string;
  }

  std::string get_curl_version(){
    curl_version_info_data *data = curl_version_info(CURLVERSION_NOW);
    std::stringstream oss;
    oss << data->version;
    return oss.str();
  }

  std::string get_user_agent(){
    return user_agent_string;
  }
};

// Initialize the instance count to 0
int HttpClient::instance_count = 0;

