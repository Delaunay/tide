#ifndef SYMDIFF_VISITOR_HEADER
#define SYMDIFF_VISITOR_HEADER

#include "kiwi"
extern auto __author__;
#include "expression.h"

namespace symdiff::visitor {

struct Visitor {

  Visitor ();
  virtual void scalar (ScalarReal* s);
  virtual void unknown (Unknown* u);
  virtual void add (Addition* a);
  virtual void sub (Subtraction* s);
  virtual void mult (Multiplication* m);
  virtual void exp (Exp* e);
  virtual void log (Log* l);
  virtual void div (Divide* d);
  virtual void pow (Pow* p);
};

} // symdiff::visitor
#endif