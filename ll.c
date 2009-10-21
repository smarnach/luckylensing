#include <string.h>
#include <math.h>

struct ll_lens_type
{
    double x, y, theta_E;
};

struct ll_lenses_type
{
    unsigned num_lenses;
    struct ll_lens_type *lens;
};

struct ll_rect_type
{
    double x0, y0, x1, y1;
};

struct ll_magpattern_type
{
    struct ll_lenses_type lenses;
    struct ll_rect_type region;
    unsigned xpixels, ypixels;
    double pixels_per_width, pixels_per_height;
    int *count;
};

void ll_shoot_single_ray(struct ll_magpattern_type *magpat,
                         const double x, const double y)
{
    struct ll_lens_type *lens = magpat->lenses.lens;
    double x_deflect = 0.0, y_deflect = 0.0;
    for(unsigned i = 0; i < magpat->lenses.num_lenses; ++i)
    {
        double dx = x - lens[i].x;
        double dy = y - lens[i].y;
        double theta_squared = dx*dx + dy*dy;
        if (theta_squared == 0.0)
            return;
        double deflection = lens[i].theta_E*lens[i].theta_E / theta_squared;
        x_deflect -= dx * deflection;
        y_deflect -= dy * deflection;
    }
    int mag_x = floor((x + x_deflect - magpat->region.x0)
                      * magpat->pixels_per_width + 0.5);
    int mag_y = floor((y + y_deflect - magpat->region.y0)
                      * magpat->pixels_per_height + 0.5);
    if (0 <= mag_x && mag_x < magpat->xpixels &&
        0 <= mag_y && mag_y < magpat->ypixels)
        ++magpat->count[mag_y*magpat->xpixels + mag_x];
}

extern void ll_rayshoot_rect(struct ll_magpattern_type *magpat,
                             struct ll_rect_type *rect,
                             unsigned xrays, unsigned yrays)
{
    double width_per_xrays = (rect->x1 - rect->x0) / xrays;
    double height_per_yrays = (rect->y1 - rect->y0) / yrays;
    magpat->pixels_per_width = magpat->xpixels
        / (magpat->region.x1 - magpat->region.x0);
    magpat->pixels_per_height = magpat->ypixels
        / (magpat->region.y1 - magpat->region.y0);
    for (unsigned j = 0; j <= yrays; ++j)
        for (unsigned i = 0; i <= xrays; ++i)
            ll_shoot_single_ray(magpat,
                                rect->x0 + i*width_per_xrays,
                                rect->y0 + j*height_per_yrays);
}

extern void ll_image_from_magpat(char buf[], struct ll_magpattern_type *magpat)
{
    int max_count = 0;
    int min_count = MAXINT;
    for(unsigned i = 0; i < magpat->xpixels*magpat->ypixels; ++i)
    {
        if (magpat->count[i] > max_count)
            max_count = magpat->count[i];
        if (magpat->count[i] < min_count)
            min_count = magpat->count[i];
    }
    if (max_count == min_count)
        return;
    double logmax = log(max_count+1);
    double logmin = log(min_count+1);
    double factor = 255/(logmax-logmin);
    for(unsigned i = 0; i < magpat->xpixels*magpat->ypixels; ++i)
        buf[i] = (log(magpat->count[i]+1)-logmin)*factor;
}
