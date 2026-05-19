#include <iostream>
#include <string>
using namespace std;

void mostrarMensaje(string mensaje) {
    cout << mensaje << endl;
}

float calcularPotencia(float base, int exponente) {
    float resultado = 1.0;
    int i = 0;
    if (i < exponente) {
    resultado = resultado * base;
    i = i + 1;
}
return resultado;
}

void duplicarValores(int valorA, int valorB) {
    valorA = valorA * 2;
    valorB = valorB * 2;
    cout << valorA << endl;
    cout << valorB << endl;
}


int main() {
    float a;
    float b;
    float base;
    int contador;
    float division;
    int exp;
    int exponente;
    int i;
    int j;
    string mensaje;
    float multiplicacion;
    int num1;
    int num2;
    int opcion;
    float res;
    float resta;
    float resultado;
    float suma;
    int valorA;
    int valorB;

    opcion = 1;
    do {
        cout << "MENU DE OPERACIONES C++" << endl;
        cout << "1. Operaciones matematicas basicas" << endl;
        cout << "2. Demostracion while" << endl;
        cout << "3. Demostracion for" << endl;
        cout << "4. Uso de funciones" << endl;
        cout << "5. Uso de procedimientos" << endl;
        cout << "9. Salir" << endl;
        switch (opcion) {
        case 1:
            a = 15.5;
            b = 4.5;
            suma = a + b;
            resta = a - b;
            multiplicacion = a * b;
            division = a / b;
            cout << suma << endl;
            cout << resta << endl;
            cout << multiplicacion << endl;
            cout << division << endl;
        case 2:
            contador = 1;
            while (contador <= 5) {
                cout << contador << endl;
                contador = contador + 1;
            }  // fin while
        case 3:
            j = 2;
            while (j <= 10) {
                cout << j << endl;
                j = j + 2;
            }  // fin for
        case 4:
            base = 2.0;
            exp = 3;
            auto t13 = calcularPotencia(base, exp);
            res = t13;
            cout << res << endl;
        case 5:
            num1 = 10;
            num2 = 25;
            auto t14 = duplicarValores(num1, num2);
        case 9:
            auto t15 = mostrarMensaje("saliendo del programa con exito");
        default:
            auto t16 = mostrarMensaje("opcion invalida intente de nuevo");
        }  // fin switch
        opcion = 9;
    } while (opcion != 9);
    return 0;
}