#pragma once

#include <boost/program_options.hpp>

class CommandLineProcessor {
 private:
  boost::program_options::variables_map argv_vm;
  boost::program_options::options_description desc;

 public:
  CommandLineProcessor(int ac, char* av[]) : desc("Allowed options") {
    desc.add_options()("help,h", "produce help message")(
        "zipcode,z", boost::program_options::value<std::string>())(
        "days,d", boost::program_options::value<int>());

    boost::program_options::positional_options_description p;
    p.add("zipcode", -1);
    boost::program_options::store(
        boost::program_options::command_line_parser(ac, av)
            .options(desc)
            .allow_unregistered()
            .style(
                boost::program_options::command_line_style::unix_style |
                boost::program_options::command_line_style::allow_long_disguise)
            .positional(p)
            .run(),
        argv_vm);
    boost::program_options::notify(argv_vm);
  }

  bool hasHelp() const { return argv_vm.count("help"); }
  bool hasDays() const { return argv_vm.count("days"); }
  bool hasZipCode() const { return argv_vm.count("zipcode"); }
};