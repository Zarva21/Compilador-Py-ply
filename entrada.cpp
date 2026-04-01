#include <iostream>
#include <string>
using namespace std;

int doble(int x) {
    auto t1 = x * 2;
    return t1;
}

int triple(int x) {
    auto t2 = doble(x);
    auto t3 = t2 + x;
    return t3;
}

int factorial(int n) {
    if (n == 0) {
    return 1;
    auto t14 = n - 1;
    auto t13 = factorial(t14);
    auto t15 = n * t13;
    return t15;
}


int main() {
    int a;
    int b;
    int globalvar;
    int resultado;
    int x;
    float y;
    string z;

        x = 10;
        cout << x << endl;
        y = 3.14;
        z = "hola";
        if (x > 5) {
            a = 20;
        } else {
            b = 30;
        }  // fin else
        globalvar = 100;
        while (x > 0) {
            auto t5 = x + 2;
            if (t5 == 0) {
                cout << x << endl;
            } else {
                cout << 0 << endl;
            }  // fin else
            x = x - 1;
        }  // fin while
        auto t8 = x + y;
        auto t9 = x - 2;
        auto t10 = t8 * t9;
        resultado = t10 / 3;
    return 0;
}