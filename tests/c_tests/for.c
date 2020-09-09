//usr/bin/gcc-8 "$0" -o "$0".bin && exec ./"$0".bin

int f1(){
    for(int i = 0; i < 10; i++){

    }
}

int f2(){
    for(int i = 0, n = 10; i < n; i++){

    }
}

int f3(){
    int i = 0;
    for(;;){
        if (i > 10)
            break;

        i++;
    }
}

int f4(){
    while (1){

    }
}

int f5(){
    do {

    } while (1);
}

int main(int argc, const char* argv[]){
    
    return 0;
}
