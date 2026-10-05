#include <iostream>
#include <string>
using namespace std;

int cuadrado(int n) {
    auto t0 = n * n;
    return t0;
}


int main() {
    int contador;
    int valor;

        contador = 0;
        while (contador < 5) {
            auto t2 = cuadrado(contador);
            valor = t2;
            switch (valor) {
            case 0:
                cout << valor << endl;
                break;
            case 1:
                cout << valor << endl;
                break;
            default:
                cout << valor << endl;
            }  // fin switch
            contador = contador + 1;
        }  // fin while
    return 0;
}