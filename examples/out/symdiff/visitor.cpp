#include "visitor.h"
auto __author__ = "Pierre Delaunay";

namespace symdiff::visitor {

Visitor::Visitor () {

}
void Visitor::scalar (ScalarReal* s) {
  throw None;
}
void Visitor::unknown (Unknown* u) {
  throw None;
}
void Visitor::add (Addition* a) {
  throw None;
}
void Visitor::sub (Subtraction* s) {
  throw None;
}
void Visitor::mult (Multiplication* m) {
  throw None;
}
void Visitor::exp (Exp* e) {
  throw None;
}
void Visitor::log (Log* l) {
  throw None;
}
void Visitor::div (Divide* d) {
  throw None;
}
void Visitor::pow (Pow* p) {
  throw None;
}

} // symdiff::visitor