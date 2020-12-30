#include "point.h"

namespace containers::point {

void add (float a, float b) {
  return math::add(a, b);
}
Point::Point (float x, float y) {
  this->x = x;
  this->y = y;
}
void Point::sum () {
  return this->x + this->y;
}
Point::~Point () {
  return ;
}
void Point::astuple () {
  return std::make_tuple(this->x, this->y);
}
void Point::operator == (Point const& other) const {
  return this->x == other.x && this->y == other.y;
}
void Point::operator - (Point const& other) const {
  return Point(this->x - other.x, this->y - other.y);
}
void Point::operator + (Point const& other) const {
  return Point(this->x + other.x, this->y + other.y);
}
void Point::operator * (Point const& other) const {
  return Point(this->x * other.x, this->y * other.y);
}
void Point::dot (Point const& other) {
  return this->x * other.x + this->y * other.y;
}
void Point::other () {

}
void Point::dist () {
  return math::sqrt(this->dot(this));
}
void Point::distance (Point const& a, Point const& b) {
  auto v = a - b;
  return v.dist();
}
Point zero = Point(0, 0);
int __main__(int argc, const char* argv[]) {
  auto p = Point(2.0, 1.0);
  return 0;
}

} // containers::point