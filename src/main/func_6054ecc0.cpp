struct Pair { int first; int second; };
struct Holder { int pad; Pair p; };

extern "C" void func_6054ecc0(Holder* h, int value)
{
    if (h->p.first != value) {
        h->p = Pair{value, 0};
    }
}