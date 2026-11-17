extern "C" char D_618344e4;

struct Node { char *p; };

extern "C" void func_61379124(int *, ...);

extern "C" void func_61354780(int *a) {
    char *v = &D_618344e4 + 8;
    *a = (int)v;
    func_61379124(a);
}