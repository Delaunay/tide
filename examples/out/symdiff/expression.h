#ifndef SYMDIFF_EXPRESSION_HEADER
#define SYMDIFF_EXPRESSION_HEADER

#include "kiwi"
extern auto __author__;
#include <cmath>

namespace symdiff::expression {

struct Expression {

  Expression ();
  virtual str __repr__ ();
  virtual str __str__ ();
  virtual bool operator == (Expression* other);
  virtual Expression* derivate (str x);
  virtual bool is_scalar ();
  virtual bool is_one ();
  virtual bool is_nul ();
  virtual bool is_leaf ();
  virtual Expression* eval (Dict variables);
  virtual float full_eval (Dict variables);
  virtual Expression* operator * (Expression* other);
  virtual Expression* operator + (Expression* other);
  virtual Expression* __truediv__ (Expression* other);
  virtual Expression* __pow__ (Expression* other);
  virtual Expression* operator - (Expression* other);
  virtual Expression* __neg__ ();
  virtual void variables ();
  virtual void get_tree ();
  virtual Expression* apply_function (str function);
  virtual Expression* copy ();
  virtual Expression* simplify ();
  virtual Expression* develop ();
  virtual Expression* factorize ();
  virtual Expression* cancel ();
  virtual void _print ();
  virtual int _id ();
  virtual bool operator < (Expression* other);
};
Tuple reorder (Expression* a, Expression* b);
struct UnaryOperator: public Expression {
  Expression expr;

  UnaryOperator (Expression* expr);
  virtual bool operator == (Expression* other);
  virtual void variables ();
  virtual void get_tree ();
};
struct BinaryOperator: public Expression {
  Expression* left;
  Expression* right;

  BinaryOperator (Expression* left, Expression* right);
  virtual bool operator == (Expression* other);
  virtual void variables ();
  virtual void get_tree ();
};
struct ScalarReal: public Expression {
  float value;

  ScalarReal (float value);
  virtual str __str__ ();
  virtual str __repr__ ();
  virtual Expression* __neg__ ();
  virtual bool operator == (Expression* other);
  virtual bool is_scalar ();
  virtual bool is_one ();
  virtual bool is_nul ();
  virtual bool is_leaf ();
  virtual Expression* derivate (Expression* x);
  virtual void eval (Dict variables);
  virtual Expression* full_eval (Dict variables);
  virtual Expression* apply_function (str function);
  virtual int _id ();
};
extern Expression* __one;
extern Expression* __zero;
extern Expression* __minus_one;
extern Expression* __two;
Expression* one ();
Expression* zero ();
Expression* minus_one ();
Expression* two ();
struct Unknown: public Expression {
  str name;
  int size;

  Unknown (str name, tuple size);
  virtual str __repr__ ();
  virtual str __hash__ ();
  virtual str __str__ ();
  virtual int _id ();
  virtual bool is_leaf ();
  virtual Expression* derivate (Expression* x);
  virtual Expression* eval (Dict variables);
  virtual Expression* full_eval (Dict variables);
  virtual void variables ();
};
struct Addition: public BinaryOperator {

  Addition (Expression* left, Expression* right);
  virtual str __str__ ();
  virtual str __repr__ ();
  virtual Expression* derivate (Expression* x);
  virtual Expression* eval (Dict variables);
  virtual Expression* full_eval (Dict variables);
  virtual void apply_function (str function);
  virtual int _id ();
};
struct Subtraction: public BinaryOperator {

  Subtraction (Expression* left, Expression* right);
  virtual str __str__ ();
  virtual str __repr__ ();
  virtual Expression* derivate (Expression* x);
  virtual Expression* eval (Dict variables);
  virtual Expression* full_eval (Dict variables);
  virtual Expression* apply_function (str function);
  virtual int _id ();
};
struct Multiplication: public BinaryOperator {

  Multiplication (Expression* left, Expression* right);
  virtual str __str__ ();
  virtual str __repr__ ();
  virtual Expression* derivate (Expression* x);
  virtual Expression* eval (Dict variables);
  virtual Expression* full_eval (Dict variables);
  virtual Expression* apply_function (str function);
  virtual Expression* copy ();
  virtual Expression* simplify ();
  virtual Expression* develop ();
  virtual int _id ();
};
struct Exp: public UnaryOperator {

  Exp (Expression* expr);
  virtual str __str__ ();
  virtual str __repr__ ();
  virtual Expression* derivate (Expression* x);
  virtual Expression* eval (Dict variables);
  virtual Expression* full_eval (Dict variables);
  virtual void apply_function (str function);
  virtual Expression* cancel ();
  virtual int _id ();
};
struct Log: public UnaryOperator {

  Log (Expression* expr);
  virtual str __str__ ();
  virtual str __repr__ ();
  virtual Expression* derivate (Expression* x);
  virtual Expression* eval (Dict variables);
  virtual Expression* full_eval (Dict variables);
  virtual Expression* apply_function (str function);
  virtual Expression* cancel ();
  virtual int _id ();
};
struct Divide: public BinaryOperator {

  Divide (Expression* up, Expression* down);
  virtual str __str__ ();
  virtual str __repr__ ();
  virtual Expression* up ();
  virtual Expression* down ();
  virtual Expression* derivate (Expression* x);
  virtual Expression* eval (Dict variables);
  virtual Expression* full_eval (Dict variables);
  virtual Expression* apply_function (str function);
  virtual int _id ();
};
struct Pow: public BinaryOperator {

  Pow (Expression* expr, Expression* power);
  virtual Expression* power ();
  virtual Expression* expr ();
  virtual str __str__ ();
  virtual str __repr__ ();
  virtual Expression* derivate (Expression* x);
  virtual Expression* eval (Dict variables);
  virtual Expression* full_eval (Dict variables);
  virtual Expression* apply_function (str function);
  virtual int _id ();
};
struct MathConstant: public ScalarReal {
  str name;

  MathConstant (str name, float value);
  virtual str __str__ ();
  virtual str __repr__ ();
  virtual void copy ();
  virtual int _id ();
};
extern auto __euler;
extern auto __pi;
Expression* pi ();
Expression* e ();
Expression* add (Expression* l, Expression* r);
Expression* mult (Expression* l, Expression* r);
Expression* exp (Expression* expr);
Expression* pow (Expression* expr, Expression* power);
Expression* log (Expression* expr);
Expression* div (Expression* up, Expression* down);
Expression* scalar (float v);
Expression* sub (Expression* l, Expression* r);
int __main__(int argc, const char* argv[]);

} // symdiff::expression
#endif