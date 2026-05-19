#include <iostream>
#include <string>
using namespace std;

int main() {
    int a;
    int b;
    char d;

    a = 5;
    b = 10;
    d = 'z';
    a = a + b;
    cout << "valor de c" << endl;
    cout << "inicio del programa" << endl;
    if (a > 3) {
        cout << "a es mayor que 3" << endl;
    }  // fin if
    while (a < b) {
        cout << "loop ejecutandose" << endl;
        a = a + 1;
    }  // fin while
    cout << "fin del programa" << endl;
    return 0;
}