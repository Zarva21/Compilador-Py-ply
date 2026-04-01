#include <iostream>
#include <string>
using namespace std;

int main() {
    int bandera;
    int bandera2;
    int resultado;
    int x;
    int y;

        auto t0 = x + y;
        auto t1 = x - 1;
        x = 5;
        y = 3;
        resultado = 0;
        resultado = t0;
        cout << resultado << endl;
        if (resultado > 5) {
            bandera = 1;
        } else {
            bandera2 = 0;
        }  // fin else
        while (x > 0) {
            x = t1;
            cout << x << endl;
        }  // fin while
    return 0;
}