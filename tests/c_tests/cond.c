//usr/bin/gcc-8 "$0" -o "$0".bin && exec ./"$0".bin


void c1(){
    if (1){

    } else if (2) {

    } else {
        
    }
}


void c2(){
    switch(1){
        case 0: 
            break;
        case 1:
        case 2:
            break;
        case 3:
            break;
        default:
            break;
    }
}

void c3(){
    int a = 1 ? 2 : 3;
}

int main(int argc, const char* argv[]){
    return 0;
}
