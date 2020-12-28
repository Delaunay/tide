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
  return other.x == this->x && other.y == this->y;
}
void Point::other () {

}
float Point::dist (Point a, Point b) {
  auto v = a - b;
  return math::sqrt(v * v);
}

} // containers::point