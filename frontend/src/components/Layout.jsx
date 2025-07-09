import React, { useState } from 'react';
import { Outlet, Link, useLocation, useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import NotificationCenter from './NotificationCenter';
import { Button } from '@/components/ui/button';
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import {
  Sheet,
  SheetContent,
  SheetTrigger,
} from '@/components/ui/sheet';
import {
  Home,
  FileText,
  Users,
  Settings,
  LogOut,
  Menu,
  MessageSquare,
  Calendar,
  BarChart3,
  HelpCircle,
  Bell,
  Upload,
  CheckCircle,
  Clock,
  AlertCircle,
} from 'lucide-react';

const Layout = () => {
  const { user, logout, isAdmin, isManager, isSpeaker } = useAuth();
  const location = useLocation();
  const navigate = useNavigate();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const getInitials = (firstName, lastName) => {
    return `${firstName?.charAt(0) || ''}${lastName?.charAt(0) || ''}`.toUpperCase();
  };

  const getNavigationItems = () => {
    const items = [];

    if (isSpeaker()) {
      items.push(
        { name: 'Dashboard', href: '/speaker', icon: Home },
        { name: 'Submit Session', href: '/speaker/sessions/new', icon: Upload },
        { name: 'FAQ', href: '/speaker/faq', icon: HelpCircle },
      );
    }

    if (isManager() || isAdmin()) {
      items.push(
        { name: 'Manager Dashboard', href: '/manager', icon: Home },
        { name: 'Questions', href: '/manager/questions', icon: MessageSquare },
        { name: 'Schedule', href: '/manager/schedule', icon: Calendar },
      );
    }

    if (isAdmin()) {
      items.push(
        { name: 'Admin Dashboard', href: '/admin', icon: BarChart3 },
        { name: 'User Management', href: '/admin/users', icon: Users },
        { name: 'FAQ Management', href: '/admin/faq', icon: HelpCircle },
        { name: 'Broadcast Messages', href: '/admin/messages', icon: Bell },
        { name: 'System Stats', href: '/admin/stats', icon: BarChart3 },
      );
    }

    return items;
  };

  const navigationItems = getNavigationItems();

  const isActiveRoute = (href) => {
    return location.pathname === href || location.pathname.startsWith(href + '/');
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'approved':
      case 'scheduled':
        return <CheckCircle className="h-4 w-4 text-green-500" />;
      case 'submitted':
      case 'under_review':
        return <Clock className="h-4 w-4 text-yellow-500" />;
      case 'rejected':
        return <AlertCircle className="h-4 w-4 text-red-500" />;
      default:
        return <FileText className="h-4 w-4 text-gray-500" />;
    }
  };

  const NavigationContent = ({ mobile = false }) => (
    <nav className={`${mobile ? 'space-y-2' : 'space-y-1'}`}>
      {navigationItems.map((item) => {
        const Icon = item.icon;
        const isActive = isActiveRoute(item.href);
        
        return (
          <Link
            key={item.name}
            to={item.href}
            onClick={() => mobile && setMobileMenuOpen(false)}
            className={`
              group flex items-center px-3 py-2 text-sm font-medium rounded-md transition-colors
              ${isActive
                ? 'bg-primary text-primary-foreground'
                : 'text-muted-foreground hover:text-foreground hover:bg-accent'
              }
            `}
          >
            <Icon className={`mr-3 h-5 w-5 ${isActive ? 'text-primary-foreground' : 'text-muted-foreground group-hover:text-foreground'}`} />
            {item.name}
          </Link>
        );
      })}
    </nav>
  );

  return (
    <div className="min-h-screen bg-background">
      {/* Desktop Sidebar */}
      <div className="hidden lg:fixed lg:inset-y-0 lg:flex lg:w-64 lg:flex-col">
        <div className="flex flex-col flex-grow bg-card border-r border-border pt-5 pb-4 overflow-y-auto">
          <div className="flex items-center flex-shrink-0 px-4">
            <div className="flex items-center">
              <div className="h-8 w-8 bg-primary rounded-lg flex items-center justify-center">
                <span className="text-primary-foreground font-bold text-sm">C</span>
              </div>
              <div className="ml-3">
                <h1 className="text-lg font-semibold text-foreground">Cybercon 2025</h1>
                <p className="text-xs text-muted-foreground">Speaker Portal</p>
              </div>
            </div>
          </div>
          <div className="mt-8 flex-grow flex flex-col">
            <div className="flex-1 px-4">
              <NavigationContent />
            </div>
          </div>
        </div>
      </div>

      {/* Mobile Header */}
      <div className="lg:hidden">
        <div className="flex items-center justify-between h-16 px-4 bg-card border-b border-border">
          <div className="flex items-center">
            <Sheet open={mobileMenuOpen} onOpenChange={setMobileMenuOpen}>
              <SheetTrigger asChild>
                <Button variant="ghost" size="sm">
                  <Menu className="h-6 w-6" />
                </Button>
              </SheetTrigger>
              <SheetContent side="left" className="w-64">
                <div className="flex items-center mb-8">
                  <div className="h-8 w-8 bg-primary rounded-lg flex items-center justify-center">
                    <span className="text-primary-foreground font-bold text-sm">C</span>
                  </div>
                  <div className="ml-3">
                    <h1 className="text-lg font-semibold text-foreground">Cybercon 2025</h1>
                    <p className="text-xs text-muted-foreground">Speaker Portal</p>
                  </div>
                </div>
                <NavigationContent mobile />
              </SheetContent>
            </Sheet>
            <h1 className="ml-4 text-lg font-semibold text-foreground">Cybercon 2025</h1>
          </div>
          <div className="flex items-center space-x-2">
            {/* Notification Center */}
            <NotificationCenter />
            
            {/* Mobile User Menu */}
            <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="ghost" className="relative h-8 w-8 rounded-full">
                <Avatar className="h-8 w-8">
                  <AvatarImage src={user?.avatar_url} alt={user?.email} />
                  <AvatarFallback>{getInitials(user?.first_name, user?.last_name)}</AvatarFallback>
                </Avatar>
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent className="w-56" align="end" forceMount>
              <DropdownMenuLabel className="font-normal">
                <div className="flex flex-col space-y-1">
                  <p className="text-sm font-medium leading-none">
                    {user?.first_name} {user?.last_name}
                  </p>
                  <p className="text-xs leading-none text-muted-foreground">
                    {user?.email}
                  </p>
                </div>
              </DropdownMenuLabel>
              <DropdownMenuSeparator />
              <DropdownMenuItem onClick={handleLogout}>
                <LogOut className="mr-2 h-4 w-4" />
                <span>Log out</span>
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>
      </div>

      {/* Main Content */}
      <div className="lg:pl-64">
        {/* Desktop Header */}
        <div className="hidden lg:flex lg:items-center lg:justify-between lg:h-16 lg:px-6 lg:bg-card lg:border-b lg:border-border">
          <div className="flex-1" />
          
          <div className="flex items-center space-x-4">
            {/* Notification Center */}
            <NotificationCenter />
            
            {/* Desktop User Menu */}
            <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="ghost" className="relative h-8 w-8 rounded-full">
                <Avatar className="h-8 w-8">
                  <AvatarImage src={user?.avatar_url} alt={user?.email} />
                  <AvatarFallback>{getInitials(user?.first_name, user?.last_name)}</AvatarFallback>
                </Avatar>
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent className="w-56" align="end" forceMount>
              <DropdownMenuLabel className="font-normal">
                <div className="flex flex-col space-y-1">
                  <p className="text-sm font-medium leading-none">
                    {user?.first_name} {user?.last_name}
                  </p>
                  <p className="text-xs leading-none text-muted-foreground">
                    {user?.email}
                  </p>
                  <div className="flex flex-wrap gap-1 mt-2">
                    {user?.roles?.map((role) => (
                      <span
                        key={role.id}
                        className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-primary/10 text-primary"
                      >
                        {role.name}
                      </span>
                    ))}
                  </div>
                </div>
              </DropdownMenuLabel>
              <DropdownMenuSeparator />
              <DropdownMenuItem onClick={handleLogout}>
                <LogOut className="mr-2 h-4 w-4" />
                <span>Log out</span>
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>

        {/* Page Content */}
        <main className="flex-1">
          <div className="py-6">
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
              <Outlet />
            </div>
          </div>
        </main>
      </div>
    </div>
  );
};

export default Layout;

