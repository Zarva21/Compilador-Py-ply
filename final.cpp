#include <iostream>
#include <string>
using namespace std;

int doble(int a) {
    auto t3 = a * 2;
    return t3;
}


int main() {
    int a;
    bool activo;
    char letra;
    string nombre;
    int r;
    int x;
    int y;

        x = 10;
        nombre = "Juan ";
        letra = 'a';
        activo = true;
        cout << " inicio " << endl;
        if (x > 5) {
            y = 2;
            cout << y << endl;
        }  // fin if
        while (x > 0) {
            x = x - 1;
        }  // fin while
        auto t4 = doble(x);
        r = t4;
        cout << r << endl;
    return 0;
}