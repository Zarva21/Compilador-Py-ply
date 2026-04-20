#include <iostream>
#include <string>
using namespace std;

int factorial(int n) {
    if (n == 0) {
    return 1;
} else {
    auto t2 = n - 1;
    auto t1 = factorial(t2);
    auto t3 = n * t1;
    return t3;
}
}


int main() {
    int r;

        auto t4 = factorial(5);
        r = t4;
        cout << r << endl;
    return 0;
}