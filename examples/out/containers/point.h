#ifndef CONTAINERS_POINT_HEADER
#define CONTAINERS_POINT_HEADER

#include "kiwi"
#include "tide/runtime/kiwi.h"
#include "myproject/math.h"
using math = myproject::math;

namespace containers::point {

float add (float a, float b);

} // containers::point
#include "myproject/math.h"

namespace containers::point {

struct Point {
  float x;
  float y;

  Point (float x, float y);
  float sum ();
  ~Point ();
  bool operator == (Point const& other) const;
  Point operator - (Point const& other) const;
  Point operator + (Point const& other) const;
  Point operator * (Point const& other) const;
  float dot (Point const& other);
  void other ();
  float dist ();
  static float distance (Point const& a, Point const& b);
};
extern Point zero;
int __main__(int argc, const char* argv[]);

} // containers::point
#endif