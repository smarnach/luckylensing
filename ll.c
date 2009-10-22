#include <values.h>
#include <math.h>
#include <stdbool.h>
#include <stdio.h>

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

inline bool __attribute__ ((hot))
ll_shoot_single_ray_double(struct ll_magpattern_type *magpat,
                           double x, double y, double *mag_x, double *mag_y)
{
    struct ll_lens_type *lens = magpat->lenses.lens;
    double x_deflect = 0.0, y_deflect = 0.0;
    for(unsigned i = 0; i < magpat->lenses.num_lenses; ++i)
    {
        double dx = x - lens[i].x;
        double dy = y - lens[i].y;
        double theta_squared = dx*dx + dy*dy;
        if (theta_squared == 0.0)
            return false;
        double deflection = lens[i].theta_E*lens[i].theta_E / theta_squared;
        x_deflect -= dx * deflection;
        y_deflect -= dy * deflection;
    }
    *mag_x = (x + x_deflect - magpat->region.x0) * magpat->pixels_per_width;
    *mag_y = (y + y_deflect - magpat->region.y0) * magpat->pixels_per_height;
    return true;
}

inline bool __attribute__ ((hot))
ll_shoot_single_ray(struct ll_magpattern_type *magpat,
                    double x, double y, int *mag_x, int *mag_y)
{
    double mag_x_d, mag_y_d;
    if (!ll_shoot_single_ray_double(magpat, x, y, &mag_x_d, &mag_y_d))
        return false;
    *mag_x = floor(mag_x_d + 0.5);
    *mag_y = floor(mag_y_d + 0.5);
    return (0 <= *mag_x && *mag_x < magpat->xpixels &&
            0 <= *mag_y && *mag_y < magpat->ypixels);
}

extern void __attribute__ ((hot))
ll_rayshoot_rect(struct ll_magpattern_type *magpat,
                 const struct ll_rect_type *rect,
                 unsigned xrays, unsigned yrays)
{
    double width_per_xrays = (rect->x1 - rect->x0) / xrays;
    double height_per_yrays = (rect->y1 - rect->y0) / yrays;
    magpat->pixels_per_width = magpat->xpixels
        / (magpat->region.x1 - magpat->region.x0);
    magpat->pixels_per_height = magpat->ypixels
        / (magpat->region.y1 - magpat->region.y0);
    int mag_x, mag_y;
    for (unsigned j = 0; j < yrays; ++j)
        for (unsigned i = 0; i < xrays; ++i)
            if (ll_shoot_single_ray(magpat,
                                    rect->x0 + i*width_per_xrays,
                                    rect->y0 + j*height_per_yrays,
                                    &mag_x, &mag_y))
                ++magpat->count[mag_y*magpat->xpixels + mag_x];
}

extern void __attribute__ ((hot))
ll_rayshoot(struct ll_magpattern_type *magpat,
            struct ll_rect_type *rect,
            unsigned xrays, unsigned yrays,
            unsigned levels)
{
    if (levels)
    {
        double width_per_xrays = (rect->x1 - rect->x0) / xrays;
        double height_per_yrays = (rect->y1 - rect->y0) / yrays;
        magpat->pixels_per_width = magpat->xpixels
            / (magpat->region.x1 - magpat->region.x0);
        magpat->pixels_per_height = magpat->ypixels
            / (magpat->region.y1 - magpat->region.y0);
        bool hit[(xrays+1)*(yrays+1)];
        int mag_x, mag_y;
        for (unsigned j = 0, m = 0; j <= yrays; ++j)
            for (unsigned i = 0; i <= xrays; ++i, ++m)
                hit[m] = ll_shoot_single_ray(magpat,
                                             rect->x0 + i*width_per_xrays,
                                             rect->y0 + j*height_per_yrays,
                                             &mag_x, &mag_y);
        for (unsigned j = 0, m = 0; j <= yrays; ++j)
            for (unsigned i = 0; i <= xrays; ++i, ++m)
            {
                if (hit[m])
                {
                    if (i)
                        hit[m-1] = true;
                    if (j)
                        hit[m-xrays-1] = true;
                }
                if ((i < xrays) && hit[m+1] ||
                    (j < yrays) && hit[m+xrays+1])
                    hit[m] = true;
            }
        for (unsigned j = 0, m = 0; j < yrays; ++j, ++m)
            for (unsigned i = 0; i < xrays; ++i, ++m)
                if (hit[m] || hit[m+1] || hit[m+xrays+1] || hit[m+xrays+2])
                {
                    double x = rect->x0 + i*width_per_xrays;
                    double y = rect->y0 + j*height_per_yrays;
                    struct ll_rect_type subrect
                        = {x, y, x+width_per_xrays, y+height_per_yrays};
                    ll_rayshoot(magpat, &subrect, 10, 10, levels-1);
                }
    }
    else
    {
        double ul_x, ul_y, ur_x, ur_y, ll_x, ll_y, lr_x, lr_y;
        bool ul = ll_shoot_single_ray_double(magpat, rect->x0, rect->y0,
                                             &ul_x, &ul_y);
        bool ur = ll_shoot_single_ray_double(magpat, rect->x1, rect->y0,
                                             &ur_x, &ur_y);
        bool ll =  ll_shoot_single_ray_double(magpat, rect->x0, rect->y1,
                                              &ll_x, &ll_y);
        bool lr =  ll_shoot_single_ray_double(magpat, rect->x1, rect->y1,
                                              &lr_x, &lr_y);
        if (ul && ur && ll && lr &&
            -0.5 <= ul_x && ul_x < magpat->xpixels + 0.5 &&
            -0.5 <= ul_y && ul_y < magpat->ypixels + 0.5 &&
            -0.5 <= ur_x && ur_x < magpat->xpixels + 0.5 &&
            -0.5 <= ur_y && ur_y < magpat->ypixels + 0.5 &&
            -0.5 <= ll_x && ll_x < magpat->xpixels + 0.5 &&
            -0.5 <= ll_y && ll_y < magpat->ypixels + 0.5 &&
            -0.5 <= lr_x && lr_x < magpat->xpixels + 0.5 &&
            -0.5 <= lr_y && lr_y < magpat->ypixels + 0.5)
        {
            double ldown_x = (ll_x - ul_x) * 0.05;
            double ldown_y = (ll_y - ul_y) * 0.05;
            double rdown_x = (lr_x - ur_x) * 0.05;
            double rdown_y = (lr_y - ur_y) * 0.05;
            double right_x = (ur_x - ul_x) * 0.05;
            double right_y = (ur_y - ul_y) * 0.05;
            double update_x = (rdown_x - ldown_x) * 0.05;
            double update_y = (rdown_y - ldown_y) * 0.05;
            double sx = ul_x;
            double sy = ul_y;
            for (unsigned j = 0; j < 20; ++j)
            {
                double x = sx;
                double y = sy;
                for (unsigned i = 0; i < 20; ++i)
                {
                    int mag_x = floor(x + 0.5);
                    int mag_y = floor(y + 0.5);
                    ++magpat->count[mag_y*magpat->xpixels + mag_x];
                    x += right_x;
                    y += right_y;
                }
                sx += ldown_x;
                sy += ldown_y;
                right_x += update_x;
                right_y += update_y;
            }
        }
        else
            ll_rayshoot_rect(magpat, rect, 20, 20);
    }
}

extern void
ll_image_from_magpat(char buf[], struct ll_magpattern_type *magpat)
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
