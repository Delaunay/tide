#ifndef SYMDIFF_EXPRESSION_HEADER
#define SYMDIFF_EXPRESSION_HEADER

#include "kiwi"
extern auto __author__;
#include <cmath>

namespace symdiff::expression {

struct Expression {

  Expression ();
  virtual void visit ();
  virtual void __repr__ ();
  virtual void __str__ ();
  virtual void operator == (Expression* other);
  virtual void derivate (str x);
  virtual void is_scalar ();
  virtual void is_one ();
  virtual void is_nul ();
  virtual void is_leaf ();
  virtual void eval (Dict<"Expression*", "Expression*"> variables);
  virtual void full_eval (Dict<"Expression*", "Expression*"> variables);
  virtual void operator * (Expression* other);
  virtual void operator + (Expression* other);
  virtual void __truediv__ (Expression* other);
  virtual void __pow__ (Expression* other);
  virtual void operator - (Expression* other);
  virtual void __neg__ ();
  virtual void variables ();
  virtual void get_tree ();
  virtual void apply_function (str function);
  virtual void copy ();
  virtual void simplify ();
  virtual void develop ();
  virtual void factorize ();
  virtual void cancel ();
  virtual void _print ();
  virtual void _id ();
  virtual void operator < (Expression* other);
};
void reorder (Expression* a, Expression* b);
struct UnaryOperator: public Expression {
  Expression expr;

  UnaryOperator (Expression* expr);
  virtual void operator == (Expression* other);
  virtual void variables ();
  virtual void get_tree ();
};
struct BinaryOperator: public Expression {
  Expression* left;
  Expression* right;

  BinaryOperator (Expression* left, Expression* right);
  virtual void operator == (Expression* other);
  virtual void variables ();
  virtual void get_tree ();
};
struct ScalarReal: public Expression {
  float value;

  ScalarReal (float value);
  virtual void __str__ ();
  virtual void __repr__ ();
  virtual void __neg__ ();
  virtual void operator == (Expression* other);
  virtual void is_scalar ();
  virtual void is_one ();
  virtual void is_nul ();
  virtual void is_leaf ();
  virtual void derivate (Expression* x);
  virtual void eval (Dict<"Expression*", "Expression*"> variables);
  virtual void full_eval (Dict<"Expression*", "Expression*"> variables);
  virtual void apply_function (str function);
  virtual void _id ();
};
extern Expression* __one;
extern Expression* __zero;
extern Expression* __minus_one;
extern Expression* __two;
void one ();
void zero ();
void minus_one ();
void two ();
struct Unknown: public Expression {
  str name;
  int size;

  Unknown (str name, tuple size);
  virtual void __repr__ ();
  virtual void __hash__ ();
  virtual void __str__ ();
  virtual void _id ();
  virtual void is_leaf ();
  virtual void derivate (Expression* x);
  virtual void eval (Dict<"Expression*", "Expression*"> variables);
  virtual void full_eval (Dict<"Expression*", "Expression*"> variables);
  virtual void variables ();
};
struct Addition: public BinaryOperator {

  Addition (Expression* left, Expression* right);
  virtual void __str__ ();
  virtual void __repr__ ();
  virtual void derivate (Expression* x);
  virtual void eval (Dict<"Expression*", "Expression*"> variables);
  virtual void full_eval (Dict<"Expression*", "Expression*"> variables);
  virtual void apply_function (str function);
  virtual void _id ();
};
struct Subtraction: public BinaryOperator {

  Subtraction (Expression* left, Expression* right);
  virtual void __str__ ();
  virtual void __repr__ ();
  virtual void derivate (Expression* x);
  virtual void eval (Dict<"Expression*", "Expression*"> variables);
  virtual void full_eval (Dict<"Expression*", "Expression*"> variables);
  virtual void apply_function (str function);
  virtual void _id ();
};
struct Multiplication: public BinaryOperator {

  Multiplication (Expression* left, Expression* right);
  virtual void __str__ ();
  virtual void __repr__ ();
  virtual void derivate (Expression* x);
  virtual void eval (Dict<"Expression*", "Expression*"> variables);
  virtual void full_eval (Dict<"Expression*", "Expression*"> variables);
  virtual void apply_function (str function);
  virtual void copy ();
  virtual void simplify ();
  virtual void develop ();
  virtual void _id ();
};
struct Exp: public UnaryOperator {

  Exp (Expression* expr);
  virtual void __str__ ();
  virtual void __repr__ ();
  virtual void derivate (Expression* x);
  virtual void eval (Dict<"Expression*", "Expression*"> variables);
  virtual void full_eval (Dict<"Expression*", "Expression*"> variables);
  virtual void apply_function (str function);
  virtual void cancel ();
  virtual void _id ();
};
struct Log: public UnaryOperator {

  Log (Expression* expr);
  virtual void __str__ ();
  virtual void __repr__ ();
  virtual void derivate (Expression* x);
  virtual void eval (Dict<"Expression*", "Expression*"> variables);
  virtual void full_eval (Dict<"Expression*", "Expression*"> variables);
  virtual void apply_function (str function);
  virtual void cancel ();
  virtual void _id ();
};
struct Divide: public BinaryOperator {

  Divide (Expression* up, Expression* down);
  virtual void __str__ ();
  virtual void __repr__ ();
  virtual void up ();
  virtual void down ();
  virtual void derivate (Expression* x);
  virtual void eval (Dict<"Expression*", "Expression*"> variables);
  virtual void full_eval (Dict<"Expression*", "Expression*"> variables);
  virtual void apply_function (str function);
  virtual void _id ();
};
struct Pow: public BinaryOperator {

  Pow (Expression* expr, Expression* power);
  virtual void power ();
  virtual void expr ();
  virtual void __str__ ();
  virtual void __repr__ ();
  virtual void derivate (Expression* x);
  virtual void eval (Dict<"Expression*", "Expression*"> variables);
  virtual void full_eval (Dict<"Expression*", "Expression*"> variables);
  virtual void apply_function (str function);
  virtual void _id ();
};
struct MathConstant: public ScalarReal {
  str name;

  MathConstant (str name, float value);
  virtual void __str__ ();
  virtual void __repr__ ();
  virtual void copy ();
  virtual void _id ();
};
extern auto __euler;
extern auto __pi;
void pi ();
void e ();
void add (Expression* l, Expression* r);
void mult (Expression* l, Expression* r);
void exp (Expression* expr);
void pow (Expression* expr, Expression* power);
void log (Expression* expr);
void div (Expression* up, Expression* down);
void scalar (float v);
void sub (Expression* l, Expression* r);
int __main__(int argc, const char* argv[]);

} // symdiff::expression
#endif