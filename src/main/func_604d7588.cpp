extern "C" int func_604d7588(int **p) {
    int *q = *p;
    int result = *q;
    *p = q + 1;
    return result;
}