#include <iostream>
#include <string>
using namespace std;

bool esBisiesto(int anio) {
    auto t0 = anio % 4;
    auto t1 = t0 == 0;
    auto t2 = anio % 100;
    auto t3 = t2 != 0;
    auto t4 = t1 && t3;
    if (t4) {
    return true;
}
auto t5 = anio % 400;
if (t5 == 0) {
return true;
}
return false;
}

float calcularPotencia(float base, int exponente) {
    float resultado = 1;
    int k = 0;
    k = 0;
    if (k < exponente) {
    resultado = resultado * base;
    L6: ;
    k = k + 1;
}
return resultado;
}

void duplicarValores(int &valorA, int &valorB) {
    valorA = valorA * 2;
    valorB = valorB * 2;
}

void mostrarMensaje(string mensaje) {
    cout << mensaje << endl;
}


int main() {
    float a;
    float b;
    float base;
    int contador;
    float division;
    int exponente;
    int i;
    int j;
    int k;
    float multiplicacion;
    int n;
    int num1;
    int num2;
    int opcion;
    float resta;
    float resultado;
    int siguiente;
    float suma;
    int t1;
    int t2;

    opcion = 1;
    do {
        cout << "==================================" << endl;
        cout << "MENU DE OPERACIONES" << endl;
        cout << "==================================" << endl;
        cout << "1 Operaciones matematicas" << endl;
        cout << "2 While" << endl;
        cout << "3 For" << endl;
        cout << "4 Funciones" << endl;
        cout << "5 Referencias" << endl;
        cout << "6 Fibonacci" << endl;
        cout << "7 Salir" << endl;
        cout << "Seleccione opcion" << endl;
        cin >> opcion;
        switch (opcion) {
        case 1: {
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
            break;
        }
    case 2: {
        contador = 1;
        while (contador <= 5) {
            cout << contador << endl;
            contador = contador + 1;
        }  // fin while
        break;
    }
case 3: {
    i = 2;
    i = 2;
    while (i <= 10) {
        cout << i << endl;
        L14: ;
        i = i + 2;
    }  // fin for
    break;
}
case 4: {
base = 2;
exponente = 4;
auto t19 = calcularPotencia(base, exponente);
resultado = t19;
cout << resultado << endl;
break;
}
case 5: {
num1 = 10;
num2 = 25;
duplicarValores(num1, num2);
cout << num1 << endl;
cout << num2 << endl;
break;
}
case 6: {
n = 7;
auto t1 = 0;
auto t2 = 1;
siguiente = 0;
j = 1;
j = 1;
while (j <= n) {
cout << t1 << endl;
siguiente = t1 + t2;
t1 = t2;
t2 = siguiente;
L17: ;
j = j + 1;
}  // fin for
break;
}
case 7: {
mostrarMensaje("Saliendo del programa");
opcion = 7;
break;
}
default: {
mostrarMensaje("Opcion invalida");
break;
}
}  // fin switch
} while (opcion != 7);
    return 0;
}