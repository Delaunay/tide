#ifndef CONTAINERS_POINT_HEADER
#define CONTAINERS_POINT_HEADER

#include "kiwi"
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
  bool operator == (Point const& other);
  void other ();
  static float dist (Point a, Point b);
};

} // containers::point
#endif