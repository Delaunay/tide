//usr/bin/gcc-8 "$0" -o "$0".bin && exec ./"$0".bin

int fun(int a, int b){
    return a + b;
}

typedef int (*fun_ptr)(int, int);

int main(int argc, const char* argv[]){
    fun_ptr fun_ptr1 = fun;
    int (*fun_ptr2)(int, int) = fun;
    return 0;
}
