#include <iostream>
#include <string>
using namespace std;

int main() {
    int a;
    int b;
    string c;

        a = 5;
        b = 10;
        cout << " inicio del programa " << endl;
        if (a > 3) {
            cout << " a es mayor que 3 " << endl;
        }  // fin if
        while (a < b) {
            cout << " loop ejecutandose " << endl;
            a = a + 1;
        }  // fin while
        c = "x";
        cout << " fin del programa " << endl;
    return 0;
}