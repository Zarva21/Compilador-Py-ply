#include <iostream>
#include <string>
using namespace std;

int main() {
    int bandera;
    int bandera2;
    int resultado;
    int x;
    int y;

        x = 5;
        y = 3;
        resultado = 0;
        resultado = x + y;
        cout << resultado << endl;
        if (resultado > 5) {
            bandera = 1;
        } else {
            bandera2 = 0;
        }  // fin else
        while (x > 0) {
            x = x - 1;
            cout << x << endl;
        }  // fin while
    return 0;
}