#ifndef CONTAINERS_POINT_HEADER
#define CONTAINERS_POINT_HEADER

#include "kiwi"
#include "myproject/math.h"
using math = myproject::math;

namespace containers::point {

void add (float a, float b);

} // containers::point
#include "myproject/math.h"

namespace containers::point {

struct Point {
  float x;
  float y;

  Point (float x, float y);
  void sum ();
  ~Point ();
  void astuple ();
  void operator == (Point const& other) const;
  void operator - (Point const& other) const;
  void operator + (Point const& other) const;
  void operator * (Point const& other) const;
  void dot (Point const& other);
  void other ();
  void dist ();
  static void distance (Point const& a, Point const& b);
};
extern Point zero;
int __main__(int argc, const char* argv[]);

} // containers::point
#endif