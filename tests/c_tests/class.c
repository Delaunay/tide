//usr/bin/gcc-8 "$0" -o "$0".bin && exec ./"$0".bin

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define SYMDIFF_NODE_TYPE(X)\
    X(Placeholder, Placeholder)\
    X(Scalar, Scalar)\
    X(Add, Binary)\
    X(Mult, Binary)\
    X(Neg, Unary)\
    X(Inv, Unary)

// Runtime type information
enum __symdiff_RTTI{
#define SYM_ENUM(name, _) __RTTI_##name,
    SYMDIFF_NODE_TYPE(SYM_ENUM)
#undef SYM_ENUM
};

// include the count inside the node itself to simplify allocations
#define __HEAD__ \
    enum __symdiff_RTTI __type;\
    int count;

#define __BINARY_OP_HEAD__ \
    __HEAD__ \
    SymExpr _lhs; \
    SymExpr _rhs;

#define __UNARY_OP_HEAD__ \
    __HEAD__ \
    SymExpr _expr;

#define SYM_NODE(name, body) \
    struct name {\
        __HEAD__ \
    \
        body;\
    };\
    typedef struct name* name;

struct __SymExpr{   
    __HEAD__             
};

typedef struct __SymExpr*  SymExpr;

SymExpr sym_copy(SymExpr expr){
    expr->count += 1;
    return expr;
}

// this is when a copy is made but we are owning the ptr
SymExpr sym_uncopy(SymExpr expr){
    expr->count -= 1;
    return expr;
}

void sym_shared_free(SymExpr expr){
    expr->count -= 1;
    if (expr->count == 0){
        free(expr);
    }
}

struct __SymBinaryExpr {   __BINARY_OP_HEAD__   };
struct __SymUnaryExpr  {   __UNARY_OP_HEAD__    };

typedef struct __SymBinaryExpr* SymBinary;
typedef struct __SymUnaryExpr*  SymUnary;

SYM_NODE(SymPlaceholder, const char* _name)
SYM_NODE(SymScalar,      double _value)

SymExpr sym_placeholder(const char* name){
    SymPlaceholder x = malloc(1 * sizeof(struct SymPlaceholder));
    x->__type = __RTTI_Placeholder;
    x->count = 1;
    x->_name = name;
    return (SymExpr) x;
}

SymExpr sym_scalar(double value){
    SymScalar x = malloc(1 * sizeof(struct SymScalar));
    x->__type = __RTTI_Scalar;
    x->count = 1;
    x->_value = value;
    return (SymExpr) x;
}

SymExpr sym_add(SymExpr lhs, SymExpr rhs){
    SymBinary x = (SymBinary) malloc(1 * sizeof(struct __SymBinaryExpr));
    x->__type = __RTTI_Add;
    x->count = 1;
    x->_rhs = sym_copy(rhs);
    x->_lhs = sym_copy(lhs);
    return (SymExpr) x;
}

SymExpr sym_mult(SymExpr lhs, SymExpr rhs){
    SymBinary x = (SymBinary) malloc(1 * sizeof(struct __SymBinaryExpr));
    x->__type = __RTTI_Mult;
    x->count = 1;
    x->_rhs = sym_copy(rhs);
    x->_lhs = sym_copy(lhs);
    return (SymExpr) x;
}

SymExpr sym_inv(SymExpr expr){
    SymUnary x = (SymUnary) malloc(1 * sizeof(struct __SymUnaryExpr));
    x->__type = __RTTI_Inv;
    x->count = 1;
    x->_expr = sym_copy(expr);
    return (SymExpr) x;
}

SymExpr sym_neg(SymExpr expr){
    SymUnary x = (SymUnary) malloc(1 * sizeof(struct __SymUnaryExpr));
    x->__type = __RTTI_Neg;
    x->count = 1;
    x->_expr = sym_copy(expr);
    return (SymExpr) x;
}

SymExpr sym_sub(SymExpr lhs, SymExpr rhs){  
    return sym_add(lhs, sym_uncopy(sym_neg(rhs)));  
}

SymExpr sym_div(SymExpr lhs, SymExpr rhs){  
    return sym_mult(lhs, sym_uncopy(sym_inv(rhs))); 
}

void sym_free(SymExpr expr) {
    if (expr == NULL)
        return ;

    switch (expr->__type){
        // Binary Operators
        case __RTTI_Add:
        case __RTTI_Mult:{
            SymBinary x = (SymBinary) expr; 
            sym_free(x->_rhs);
            sym_free(x->_lhs); 
            x->_rhs = NULL;
            x->_lhs = NULL;
            break;
        }

        // Unary Operators
        case __RTTI_Inv:
        case __RTTI_Neg:{
            SymUnary x = (SymUnary) expr; 
            sym_free(x->_expr); 
            x->_expr = NULL;
            break;
        }

        default:
            break;
    }

    return sym_shared_free(expr);
}

void sym_print(SymExpr expr){
    if (expr == NULL){
        printf("NULL");
        return ;
    }

    switch (expr->__type){
        // Leaves
        case __RTTI_Placeholder:{
            SymPlaceholder x = (SymPlaceholder) expr;
            printf("%s", x->_name);
            return;
        }
        case __RTTI_Scalar:{
            SymScalar x = (SymScalar) expr;
            printf("%f", x->_value);
            return;
        }
        // Binary Operators
        case __RTTI_Mult:{
            SymBinary x = (SymBinary) expr;
            sym_print(x->_lhs); printf(" * "); sym_print(x->_rhs);
            return;
        }
        case __RTTI_Add:{
            SymBinary x = (SymBinary) expr;
            sym_print(x->_lhs); printf(" + "); sym_print(x->_rhs);
            return;
        }
        // Unary Operators
        case __RTTI_Inv:{
            SymUnary x = (SymUnary) expr;
            printf(" 1 / "); sym_print(x->_expr);
            return;
        }
        case __RTTI_Neg:{
            SymUnary x = (SymUnary) expr;
            printf(" - "); sym_print(x->_expr);
            return;
        }
    }
}

// Reused temporary should be uncopied because they are owned by the current node
// but current constructor always assume we are making a copy
SymExpr sym_deriv_Placeholder(const char* name, SymPlaceholder x){
    if (strcmp(x->_name, name) == 0)
        return sym_scalar(1);
    return sym_scalar(0);
}

SymExpr sym_deriv_Scalar(const char* name, SymScalar x){
    return sym_scalar(0);
}

SymExpr sym_deriv(const char* name, SymExpr expr);

SymExpr sym_deriv_Mult(const char* name, SymBinary x){
    SymExpr dlhs = sym_uncopy(sym_deriv(name, x->_lhs));
    SymExpr drhs = sym_uncopy(sym_deriv(name, x->_rhs));

    return sym_add(
        sym_uncopy(sym_mult(dlhs, x->_rhs)),
        sym_uncopy(sym_mult(drhs, x->_lhs)));
}

SymExpr sym_deriv_Add(const char* name, SymBinary x){
    return sym_add(
        sym_uncopy(sym_deriv(name, x->_lhs)),
        sym_uncopy(sym_deriv(name, x->_rhs)));
}

SymExpr sym_deriv_Inv(const char* name, SymUnary x){
    SymExpr up   = sym_uncopy(sym_deriv(name, x->_expr));
    SymExpr down = sym_uncopy(sym_mult(x->_expr, x->_expr));
    return sym_neg(sym_uncopy(sym_div(up, down)));
}

SymExpr sym_deriv_Neg(const char* name, SymUnary x){
    return sym_neg(sym_uncopy(sym_deriv(name, x->_expr)));
}

SymExpr sym_deriv(const char* name, SymExpr expr){
    // generate a switch over each nodes
    // We expect most functions to be inlined
    #define SYM_CASE(fun, node, type)\
        case __RTTI_##node:{\
            Sym##type x = (Sym##type) expr;\
            return sym_##fun##_##node(name, x);\
        }


    switch (expr->__type){
        #define X(name, type) SYM_CASE(deriv, name, type)
            SYMDIFF_NODE_TYPE(X)
        #undef X
    }

    #undef SYM_CASE
}

int main(){
    SymExpr x = sym_placeholder("x");                           // 1 alloc
    SymExpr y = sym_placeholder("y");                           // 1 alloc
    SymExpr expr = sym_mult(x, x);                              // 1 alloc

    sym_print(expr);

    SymExpr df = sym_deriv("x", expr);                          // 5 Alloc

    printf("\n");

    // Free expression
    sym_free(expr);
    sym_free(x);
    sym_free(y);

    // df should hold to the reused nodes
    sym_print(df);

    printf("\n");

    sym_free(df);

    // ==13580== 
    // ==13580== HEAP SUMMARY:
    // ==13580==     in use at exit: 0 bytes in 0 blocks
    // ==13580==   total heap usage: 9 allocs, 9 frees, 1,184 bytes allocated
    // ==13580== 
    // ==13580== All heap blocks were freed -- no leaks are possible
    // ==13580== 
    // ==13580== For counts of detected and suppressed errors, rerun with: -v
    // ==13580== ERROR SUMMARY: 0 errors from 0 contexts (suppressed: 0 from 0)

    return 0;
}