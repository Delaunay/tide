#include "point.h"

namespace containers::point {

float add (float a, float b) {
  return math::add(a, b);
}
Point::Point (float x, float y) {
  this->x = x;
  this->y = y;
}
float Point::sum () {
  return this->x + this->y;
}
Point::~Point () {
  return ;
}
bool Point::operator == (Point const& other) {
  return this->x == other.x && this->y == other.y;
}
void Point::other () {

}
float Point::dist (Point a, Point b) {
  auto v = a - b;
  return math::sqrt(v * v);
}
int __main__(int argc, const char* argv[]) {
  auto p = Point(2.0, 1.0);
  return 0;
}

} // containers::point