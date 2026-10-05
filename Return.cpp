#include <iostream>
#include <string>
using namespace std;

int sumar(int a, int b) {
    auto resultado = a + b;
    return resultado;
}

void imprimirMensaje() {
    auto mensaje = Hola;
    cout << mensaje << endl;
}


int main() {
    int total;
    int x;
    int y;

        x = 10;
        y = 20;
        auto t1 = sumar(x, y);
        total = t1;
        cout << total << endl;
        auto t2 = imprimirMensaje();
    return 0;
}